"""Logger configuration for scheduler - delegates to centralized logging."""

from app.logging import setup_logging


def setup_logger():
    """Setup logger for scheduler module."""
    return setup_logging(module_name="scheduler")
