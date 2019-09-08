"""Application root configuration
"""

# Local Imports:
from .base import BaseConfig
from .server import ServerConfig
from ..util.logging import prettify_logs

class Config(BaseConfig):
    """Top-level application configuration container
    """
    def __init__(self, raw: dict):
        # TODO: Support JSON logs for log analytic platforms
        logger_type = raw["env"].get("LOGGER_TYPE", "pretty").lower()
        if (logger_type == "pretty"):
            prettify_logs()
        elif (logger_type == "plain"):
            pass
        else:
            raise ValueError("LOGGER_TYPE must be 'pretty' (default) or 'plain'")

        self.server = ServerConfig(raw)
