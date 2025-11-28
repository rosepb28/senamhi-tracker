"""Custom exceptions for the application."""


class SenamhiTrackerError(Exception):
    """Base exception for all application errors."""

    pass


class ScraperError(SenamhiTrackerError):
    """Raised when scraping operations fail."""

    pass


class DatabaseError(SenamhiTrackerError):
    """Raised when database operations fail."""

    pass


class ValidationError(SenamhiTrackerError):
    """Raised when data validation fails."""

    pass


class ConfigurationError(SenamhiTrackerError):
    """Raised when configuration is invalid."""

    pass


class ServiceError(SenamhiTrackerError):
    """Raised when service operations fail."""

    pass
