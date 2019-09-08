"""Base class from which application (sub-)configuration objects are derived
"""

class BaseConfig:
    """(Abstract) base configuration data object

    Implements pretty-printing and basic method signatures

    TODO: Should BaseConfig be an ABC?
    """
    def __init__(self, raw: dict):
        pass

    def __str__(self):
        return '%s(\n%s\n)' % (
            type(self).__name__,
            ',\n'.join('  %s=%s' % (item[0], str(item[1]).replace('\n', '\n  ')) for item in vars(self).items())
        )
