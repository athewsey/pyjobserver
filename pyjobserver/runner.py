# Built-Ins:
from asyncio import get_event_loop, iscoroutinefunction
from concurrent.futures import ThreadPoolExecutor
import inspect
from logging import getLogger
from typing import Any, Awaitable, Callable, ClassVar, Dict, Generic, List, NamedTuple, Type, TypeVar, Union
from uuid import uuid4 as generate_guid

# External Dependencies:
from aiohttp import web, WSMsgType
from asyncio import sleep
from cachetools import TTLCache
from json import dumps as json_dumps
from pyee import AsyncIOEventEmitter
from webargs.aiohttpparser import parser

# Internal Dependencies:
from .config import Config
from .base import AbstractJobRunner, Job
from .models import BaseApiModel, BaseJobSpec, JobCreatedResult, JobProgress
from .model_processing import get_model_webargs_middleware

# TODO: Add timeouts at runner level
# TODO: Add cancellation support


class JobRunner(AbstractJobRunner):
    def __init__(self, app_config: Config, threadpool: Union[ThreadPoolExecutor,None] = None):
        super().__init__(app_config, threadpool)
        self.logger = getLogger("JobRunner")
        self.handlers: Dict[Callable] = {}
        self.spec_model_types: Dict[Type[BaseJobSpec]] = {}
        self.jobs_active: List[Job] = []
        self.jobs_cache = TTLCache(maxsize=app_config.server.jobs_cache_max, ttl=app_config.server.jobs_cache_ttl)
    
    def register_job_handler(self, type_name: str, handler: Callable[[BaseJobSpec], Awaitable[BaseApiModel]]):
        signature = inspect.signature(handler)
        SuppliedJobSpec = signature.parameters["input"].annotation
        assert iscoroutinefunction(handler), \
            "job handler must be a coroutine (async) function- Synchronous job support not yet implemented"
        assert issubclass(SuppliedJobSpec, BaseJobSpec), \
            "job handler 'input' parameter must be annotated as a subclass of base.BaseJobSpec"
        
        self.handlers[type_name] = handler
        self.spec_model_types[type_name] = SuppliedJobSpec
        self.logger.info("Registered handler for job type '%s'", type_name)

    def get_status_handler(self):
        async def status_handler(request: web.Request) -> web.Response:
            return web.json_response({ "jobsActive": len(self.jobs_active) })
        return status_handler

    async def add_job(self, spec: BaseJobSpec) -> str:
        if (len(self.jobs_active) >= self.app_config.server.jobs_max):
            raise web.HTTPTooManyRequests(
                text="Maximum parallel job limit ({}) reached: Try again later".format(self.app_config.server.jobs_max)
            )
        else:
            job_type = spec.job_type
            handler = self.handlers.get(job_type)
            if (handler is None):
                raise web.HTTPBadRequest(text="Job.job_type '{}' is not recognised".format(job_type))
            
            job_id = str(generate_guid())
            job = Job(job_id, spec, self, handler)
            async def handle_complete(result):
                return await self.on_job_complete(job_id, job, job_type, result)
            job.on("complete", handle_complete)
            async def handle_critical(err):
                return await self.on_job_critical(job_id, job, job_type, err)
            job.on("critical", handle_critical)
            async def handle_debug(msg):
                return await self.on_job_debug(job_id, job, job_type, msg)
            job.on("debug", handle_debug)
            async def handle_error(err):
                return await self.on_job_error(job_id, job, job_type, err)
            job.on("error", handle_error)
            async def handle_info(msg):
                return await self.on_job_info(job_id, job, job_type, msg)
            job.on("info", handle_info)
            async def handle_progress(progress):
                return await self.on_job_progress(job_id, job, job_type, progress)
            job.on("progress", handle_progress)
            async def handle_warning(msg):
                return await self.on_job_warning(job_id, job, job_type, msg)
            job.on("warning", handle_warning)
            self.jobs_active.append(job)
            self.jobs_cache[job_id] = job
            return job_id
        
        
    async def on_job_complete(self, job_id: str, job: Job, job_type: str, result: Any):
        self.logger.info("[Job %s - %s] COMPLETE", job_id, job_type)

    async def on_job_critical(self, job_id: str, job: Job, job_type: str, err: Exception):
        self.logger.error("[Job %s - %s] FAILED: %s", job_id, job_type, err)
        
    async def on_job_debug(self, job_id: str, job: Job, job_type: str, msg: Any):
        self.logger.debug("[Job %s - %s] %s", job_id, job_type, msg)
        
    async def on_job_error(self, job_id: str, job: Job, job_type: str, err: Exception):
        self.logger.warn("[Job %s - %s] %s", job_id, job_type, err)
        
    async def on_job_info(self, job_id: str, job: Job, job_type: str, msg: Any):
        self.logger.info("[Job %s - %s] %s", job_id, job_type, msg)
        
    async def on_job_progress(self, job_id: str, job: Job, job_type: str, progress: JobProgress):
        self.logger.debug("[Job %s - %s] progress: %d%%", job_id, job_type, progress.pct)

    async def on_job_warning(self, job_id: str, job: Job, job_type: str, msg: Any):
        self.logger.warning("[Job %s - %s] %s", job_id, job_type, msg)
    
    def get_add_job_handler(self):
        async def add_job_handler(request: web.Request) -> web.Response:
            try:
                # TODO: How to best deal with needing to do webargs twice?? :'(
                # TODO: Is it right to validate the request first before checking the # jobs in progress?
                base_spec = await parser.parse(BaseJobSpec.Schema(strict=True), request)
                SpecModel = self.spec_model_types.get(base_spec.job_type)
                if (not SpecModel):
                    raise web.HTTPBadRequest("Job.job_type '{}' is not recognised".format(base_spec.job_type))

                async def do_the_do(request: web.Request) -> web.Response:
                    job_id = await self.add_job(request.get("model"))
                    return web.json_response(body=JobCreatedResult.Schema().dumps(JobCreatedResult(job_id)).data)

                return await get_model_webargs_middleware(SpecModel.Schema(strict=True))(request, do_the_do)
            except web.HTTPException as err:
                # If the process already raises an HTTPException (or subclass), JSONify any plain text messages and
                # pass through:
                if (err.content_type == "text/plain"):
                    self.logger.debug("Converting plain text error")
                    err.text = json_dumps({
                        "ok": False,
                        "message": err.text,
                    })
                    err.content_type = "application/json"
                raise err
        return add_job_handler
    
    def get_job_status_handler(self):
        async def job_status_handler(request: web.Request) -> web.Response:
            try:
                job_id = request.match_info["id"]
                job = self.jobs_cache.get(job_id)
                if (job):
                    # TODO: Implement job status handler
                    return web.json_response({
                        "ok": True,
                        "id": job_id,
                        "warnings": ["TODO: NotImplemented"]
                    })
                else:
                    raise web.HTTPNotFound(text="No such job ID '{}'".format(job_id))
            except web.HTTPException as err:
                # If the process already raises an HTTPException (or subclass), JSONify any plain text messages and
                # pass through:
                if (err.content_type == "text/plain"):
                    self.logger.debug("Converting plain text error")
                    err.text = json_dumps({
                        "ok": False,
                        "message": err.text,
                    })
                    err.content_type = "application/json"
                raise err
        return job_status_handler
    
    def get_job_socket_handler(self):
        async def job_socket_handler(request: web.Request) -> web.Response:
            job_id = request.match_info["id"]
            job = self.jobs_cache.get(job_id)
            if (not job):
                raise web.HTTPNotFound(text="No such job ID '{}'".format(job_id))
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            # TODO: Attach event listeners to job here to publish events to websocket

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'close':
                        await ws.close()
                    else:
                        await ws.send_str(msg.data + '/answer')
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error('ws connection closed with exception %s' %
                        ws.exception())

            self.logger.info('websocket connection closed')

            return ws
        return job_socket_handler

    async def webapp(self, **kwargs) -> web.Application:
        app = web.Application(**kwargs)
        app["config"] = self.app_config
        app.router.add_get("/", self.get_status_handler())
        app.router.add_post("/", self.get_add_job_handler())
        # TODO: GET on job ID yields last relevant status as long as job is retained in cache, otherwise 404
        app.router.add_get("/{id}", self.get_job_status_handler())
        app.router.add_get("/{id}/ws", self.get_job_socket_handler())
        return app
