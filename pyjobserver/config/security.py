"""Server security configuration
"""

# Built-Ins:
from json import loads as json_loads
from logging import getLogger

# Local Imports:
from .base import BaseConfig

class SecurityConfig(BaseConfig):
    """Security (e.g. authentication) configuration container
    """
    def __init__(self, raw):
        LOGGER = getLogger(__name__)
        envusers = raw["env"].get("USERS")
        if (envusers):
            self.authentication = "basic"
            self.users = json_loads(raw["env"].get("USERS"))
        else:
            self.authentication = "none"
            LOGGER.warn("No USERS supplied - starting open (unauthenticated) server")
