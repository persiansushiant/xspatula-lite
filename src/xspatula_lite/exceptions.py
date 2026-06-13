class XspatulaError(Exception):
    """Base exception for xspatula-lite."""


class ConfigError(XspatulaError):
    """Raised when scheme/job/process metadata is invalid."""


class DispatchError(XspatulaError):
    """Raised when a process cannot be dispatched."""
