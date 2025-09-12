"""
Custom exceptions for ADT utilities.
"""


class ADTUtilsError(Exception):
    """Base exception for all ADT utilities."""
    pass


class ValidationError(ADTUtilsError):
    """Raised when validation fails."""
    pass


class ProcessingError(ADTUtilsError):
    """Raised when processing operations fail."""
    pass


class ConfigurationError(ADTUtilsError):
    """Raised when configuration is invalid."""
    pass


class PageRangeError(ADTUtilsError):
    """Raised when page range is invalid."""
    pass