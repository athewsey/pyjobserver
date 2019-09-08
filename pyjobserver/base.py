# Built-Ins:
# Enable reflexive typing for instance methods to refer to the self class:
# https://stackoverflow.com/a/33533514
from __future__ import annotations
from abc import ABC, abstractmethod
from asyncio import create_task, CancelledError, InvalidStateError
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Any, Awaitable, Callable, ClassVar, Dict, Generic, List, NamedTuple, Type, TypeVar, Union

# External Imports:
from pyee import AsyncIOEventEmitter

# Local Imports:
from .config import Config

LOGGER = getLogger(__name__)

class AbstractJobRunner(ABC):
    def __init__(self, app_config: Config, threadpool: Union[ThreadPoolExecutor,None] = None):
        super().__init__()
        self.app_config = app_config
        self.threadpool = threadpool if threadpool else ThreadPoolExecutor(app_config.server.job_runner_threads)

    @abstractmethod
    async def add_job(self, spec) -> str:
        pass


T = TypeVar("T")
S = TypeVar("S")

class Job(AsyncIOEventEmitter, Generic[T, S]):
    """Utility for executing a job in a runner, emitting data events, exposing awaitable task

    :ivar id: unique job ID for the runner
    :ivar input: input data for the job
    :ivar runner: runner in which the job is being executed
    :ivar task: (asyncio.Task) wrapping the ongoing operation

    TODO: Improve event typings
    :event critical: (Exception) a critical error has caused the job to FAIL
    :event complete: (S) the job has finished with SUCCESS
    :event error: (Exception) a non-fatal but potentially serious error has occurred
    :event warning: (Exception) an important warning/caveat
    :event info: (Any) an informative update
    :event debug: (Any) a low-level, debug-oriented update
    :event progress: (JobProgress) progress / ETA information

    TODO: Store last relevant event and expose interface to retrieve
    TODO: Maybe store all errors/warnings to notify with alongside result? Only really needed for sync pattern
    """
    def __init__(
        self,
        id: str,
        input: T,
        runner: AbstractJobRunner,
        # TODO: Typing callable kwargs?
        coro: Callable[[T, Job[T,S], ThreadPoolExecutor], Awaitable[S]],
        threadpool: Union[ThreadPoolExecutor, None] = None
    ):
        """Initialises and starts Job

        :param self: class instance
        :param id: unique job ID for the runner
        :param input: input data for the job
        :param runner: runner in which the job is being executed
        :param coro: the async function to execute with input and context, returning the result
        :param threadpool: optional threadpool to pass to coro if supplied
        """
        self.id = id
        self.input = input
        self.runner = runner
        AsyncIOEventEmitter.__init__(self)
        self.task = create_task(coro(input, self, threadpool=threadpool))

        def onTaskDone(task):
            """Task done handler to publish complete (success) & critical (fail) events"""
            try:
                err = task.exception()
                if (err):
                    self.emit("critical", err)
                else:
                    result = task.result()
                    self.emit("complete", result)
            except CancelledError as err:
                self.emit(
                    "warning",
                    CancelledError(
                        "onTaskDone called after task cancelled"
                    ).with_traceback(err.__traceback__)
                )
                LOGGER.warning("Shouldn't see onTaskDone when cancelled??")
            except InvalidStateError as err:
                self.emit(
                    "error",
                    InvalidStateError(
                        "onTaskDone called before task finished: Risk of zombie task"
                    ).with_traceback(err.__traceback__)
                )

        self.task.add_done_callback(onTaskDone)
