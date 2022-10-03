class RelintError(Exception):
    pass


class ConfigError(ValueError, RelintError):
    pass
