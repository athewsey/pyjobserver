"""Web request (de-)/serialization
"""

# Built-Ins:
from http import HTTPStatus
from json import JSONDecodeError
from logging import getLogger
import typing

# External Imports:
from aiohttp import web
from marshmallow import Schema, ValidationError
from webargs.aiohttpparser import parser

# Local Imports:
from .models import BaseApiModel

LOGGER = getLogger(__name__)

def web_response_from_model(result: BaseApiModel):
    """Construct a web response from a result payload"""
    try:
        return web.json_response(body=result.__class__.Schema().dumps(result).data)
    except ValidationError as exc:
        LOGGER.exception(exc)
        raise web.HTTPInternalServerError(
            body={ "ok": False, "errors": { "_body": "Error preparing response" } }
        )
    except Exception as exc:
        LOGGER.exception(exc)
        raise exc

def get_model_webargs_middleware(schema: Schema):
    @web.middleware # noqa: Z110
    async def model_webargs_middleware(
        request: web.Request,
        handler: typing.Callable[[web.Request], typing.Awaitable[web.Response]],
    ) -> web.Response:
        """
        Deserialize a request with webargs.

        :param request: request object
        :param handler: handler function
        :return:
        """
        try:
            model = await parser.parse(schema, request)
            request["model"] = model
            return await handler(request)
        except JSONDecodeError as exc:
            raise web.HTTPBadRequest(
                body={ "ok": False, "errors": { "_body": "Cannot deserialize JSON." } }
            ).with_traceback(exc.__traceback__)
        except ValidationError as exc:
            raise web.HTTPBadRequest(
                # TODO: Is this really correct syntax?
                body={ "ok": False, "errors": { exc.messages } }
            ).with_traceback(exc.__traceback__)
        except Exception as exc:
            LOGGER.exception(exc)
            raise exc
    return model_webargs_middleware
