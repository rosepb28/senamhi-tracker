"""Centralized logging configuration using loguru."""

import sys
from pathlib import Path

from loguru import logger

from config.settings import settings


def setup_logging(module_name: str | None = None) -> "logger":
    """
    Configure and return a logger instance.

    Args:
        module_name: Optional module name for contextualized logging

    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()

    # Console handler with colors
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    if module_name:
        log_format = log_format.replace(
            "<cyan>{name}</cyan>", f"<cyan>{module_name}</cyan>"
        )

    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    # Add file handler if log file is configured
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            settings.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG" if settings.debug else "INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )

    return logger


# Create default logger instance
default_logger = setup_logging()
