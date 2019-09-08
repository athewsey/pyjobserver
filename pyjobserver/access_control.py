"""Aiohttp microservice authentication tools

Currently only supports simple basic auth middleware
"""

# Built-Ins:
import typing

# External Imports:
from aiohttp import web
from aiohttp_basicauth_middleware import basic_auth_middleware

# Local Imports:
from .config import Config


def get_authentication_middleware(config: Config) -> typing.Callable[
        [web.Request, typing.Callable[[web.Request], typing.Awaitable[web.Response]]],
        typing.Awaitable[web.Response]
    ]:
    """Create an aiohttp.web authentication middleware as prescribed by app config, or None
    """
    policy = config.server.security.authentication
    if (policy == "basic"):
        return basic_auth_middleware(
            ("/",),
            config.server.security.users,
        )
    elif (policy == "none"):
        return None
    else:
        raise ValueError("Unrecognised authentication policy '{}' in app config".format(policy))
