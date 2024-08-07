"""Write your own linting rules using regular expressions."""

try:
    from . import _version
except ImportError:
    _version = None

__version__ = getattr(_version, 'version', 'unknown')
VERSION = getattr(_version, 'version_tuple', (0, 0, 0))
