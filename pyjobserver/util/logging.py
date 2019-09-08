"""Provide a function to colorize+prettify logging (oriented towards console viewing)

Heavily inspired by:
- https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
- The ansicolors module
- https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles
"""

# Built-Ins:
from logging import DEBUG, Formatter, Logger, setLoggerClass, StreamHandler
from string import Template

# External Dependencies:
from colors import color

# Configuration:
LEVELS = {
    "CRITICAL": {
        "name": "CRIT",
        "fg": "black",
        "bg": "red",
    },
    "ERROR": {
        "name": "ERROR",
        "fg": "red",
    },
    "WARNING": {
        "name": "WARN",
        "fg": "yellow",
    },
    "INFO": {
        "name": "INFO",
        "fg": "green",
    },
    "DEBUG": {
        "name": "DEBUG",
        "fg": "cyan",
    },
    "SILLY": {
        "name": "SILLY",
        "fg": "magenta",
    }
}

class PrettyLevelsFormatter(Formatter):
    """A colourful logging.Formatter oriented towards readable console output
    """
    def __init__(self, fmt, **kwargs):
        if (kwargs["style"] != "$"):
            # Only Templates support partial substitution, which this formatter needs. Templates use $ style syntax:
            raise ValueError("Only style='$' is supported because this formatter uses String Templates")
    
        Formatter.__init__(self, fmt, **kwargs)
        # To try and keep performant we don't want to over-complicate our format() with Python logic, so the easiest
        # way is just to create a pool of different formatters per log level:
        tFmt = Template(fmt)
        self.formatters = {
            level: Formatter(
                tFmt.safe_substitute({
                    "levelname": color(
                        LEVELS[level]["name"],
                        fg=LEVELS[level].get("fg"),
                        bg=LEVELS[level].get("bg")
                    )
                }),
                **kwargs
            )
        for level in LEVELS }

    def format(self, record):
        if (record.levelname in self.formatters):
            return self.formatters[record.levelname].format(record)
        else:
            return super().format(record)

class PrettyLogger(Logger):
    """A colourful logging.Logger oriented towards readable console output
    """
    def __init__(self, name, level=DEBUG):
        Logger.__init__(self, name, level)
        console = StreamHandler()
        console.setFormatter(PrettyLevelsFormatter(
            color("[${asctime}]", fg="grey") + " ${levelname} " + color("(${name}): ", fg="grey") + "${message}",
            style="$"
        ))
        self.addHandler(console)

def prettify_logs():
    setLoggerClass(PrettyLogger)
