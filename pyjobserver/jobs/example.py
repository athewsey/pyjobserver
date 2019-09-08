"""A dummy example job
"""

# Built-Ins:
from asyncio import sleep
from typing import Awaitable

# External Imports:
from dataclasses import field
from marshmallow import Schema
from marshmallow_dataclass import dataclass

# Internal Imports:
from ..base import Job
from ..models import BaseApiModel, BaseJobSpec, JobProgress


@dataclass
class ExampleJobSpec(BaseJobSpec):
    succeed: bool = field(metadata={ "required": True })

@dataclass
class ExampleJobResult(BaseApiModel):
    id: str = field()
    # TODO: Will this serialise properly?
    spec: ExampleJobSpec = field()
    result: bool = field()

async def example_job_fn(input: ExampleJobSpec, taskobj: Job, threadpool=None) -> ExampleJobResult:
    for i in range(5):
        await sleep(2)
        taskobj.emit("progress", JobProgress((i + 0.5) * 20))
    assert input.succeed, "Example job failing as instructed by specification"
    await sleep(2)
    return ExampleJobResult(id=taskobj.id, spec=input, result=True)
