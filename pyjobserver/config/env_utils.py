# Built-Ins:
from typing import Any

BOOLEAN_ENV_TRUE = ("1", "enable", "enabled", "on", "true", "yes")
BOOLEAN_ENV_FALSE = ("0", "disable", "disabled", "off", "false", "no")

def env_to_boolean(value_str: str) -> bool:
    """Convert a (string) environment variable to a Python bool
    
    :raises ValueError: value_str failed boolean validation
    """
    if (value_str is None):
        return False
    value_str_lower = value_str.lower()
    if (value_str_lower in BOOLEAN_ENV_TRUE):
        return True
    elif (value_str_lower in BOOLEAN_ENV_FALSE):
        return False
    else:
        raise ValueError("Environment variable failed boolean validation")

def mandatory(val: Any) -> Any:
    """Raises a ValueError if the provided input is None, otherwise returns it"""
    if (val is None):
        raise ValueError("Missing mandatory configuration value")
    return val
