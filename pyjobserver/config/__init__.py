"""Application configuration utilities

Defines schema classes, loads configuration from env vars and/or a yml manifest
"""

# Built-Ins:
from logging import getLogger as _getLogger
from os import environ as _environ
from pathlib import Path as _Path
from typing import Union

# External Imports:
from yaml import safe_load as _safe_load

# Local Imports:
from .config import Config

async def load(manifest_path: Union[_Path, None]) -> Config:
    """Configuration loader function

    This architecture balances readiness for async-requiring configuration fetches (e.g. a cloud credential store),
    with convenience of having synchronously constructed configuration objects. This way our configuration model
    classes can be nicely statically typed, at the cost of needing to make sure we have all the necessary data
    loaded & ready in time for synchronous cascading __init__ calls.
    """
    raw = {}
    if (manifest_path):
        print("Loading configuration manifest %s", manifest_path)
        with manifest_path.open() as manifest_file:
            raw = _safe_load(manifest_file)
    else:
        print("No configuration manifest supplied - using environment variables only")
    raw["env"] = _environ
    APPCONFIG = Config(raw)
    LOGGER = _getLogger(__name__)
    LOGGER.info(APPCONFIG)
    return APPCONFIG
