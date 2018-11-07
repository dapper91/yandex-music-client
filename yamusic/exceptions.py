"""Exception classes for library-related errors."""


class BaseError(Exception):
    """Base module exception"""


class AuthenticationError(BaseError):
    """Authentication error"""


class ResponseFormatError(BaseError):
    """Response formant is not correct"""


class NotFoundError(BaseError):
    """Requested object not found"""
