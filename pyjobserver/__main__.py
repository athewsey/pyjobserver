"""Main/example start-up script for the pyjobserver

Use this as a guide if importing pyjobserver into another app instead
"""

# Built-Ins:
import asyncio
from logging import getLogger, Logger
import os
from pathlib import Path

# External Dependencies:
from aiohttp import web
import click
from dotenv import load_dotenv

# Local Dependencies:
from .access_control import get_authentication_middleware
from .config import load as load_config, Config
from .jobs.example import example_job_fn
from .runner import JobRunner

# (Only entry point scripts should load dotenvs)
load_dotenv(os.getcwd() + "/.env")


async def alive_handler(request) -> web.Response:
    """Basic server aliveness indicator
    """
    return web.json_response({"ok": True})


async def init_app(config: Config, LOGGER: Logger):
    """Create an application instance.
    :return: application instance
    """
    app = web.Application(logger=LOGGER)
    app.router.add_get("/", alive_handler)
    authentication_middleware = get_authentication_middleware(config)
    runner = JobRunner(config)

    # ADD YOUR JOB TYPES LIKE THIS:
    # The job function must be conformant including the correct signature type annotations.
    runner.register_job_handler("example", example_job_fn)

    runner_app = await runner.webapp(middlewares=[authentication_middleware] if authentication_middleware else None)
    app.add_subapp("/api", runner_app)

    return app

# Note we need to separate out the main_coro from main() because click (our command line args processor) can't decorate
# async functions
async def main_coro(manifest: str):
    """Initialise and serve application.

    Function is called when the module is run directly
    """
    config = await load_config(Path(manifest) if manifest else None)
    LOGGER = getLogger(__name__)
    app = await init_app(config, LOGGER)
    runner = web.AppRunner(app, handle_signals=True)
    await runner.setup()
    site = web.TCPSite(runner, port=config.server.port)
    await site.start()
    LOGGER.info("Server running on port %i", config.server.port)

    # TODO: Are we supposed to expose the runner somehow to clean up on shutdown?
    #await runner.cleanup()

@click.command()
@click.option("--manifest", default="", help="Location of (optional) manifest file relative to current working dir")
def main(manifest: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_coro(manifest))
    loop.run_forever()

if __name__ == "__main__":
    # Linter error here is caused by PyLint not understanding the click decorator:
    main()  # pylint: disable=no-value-for-parameter
