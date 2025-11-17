"""Logging configuration for scheduler."""

import logging
import sys
from pathlib import Path

from config.config import settings


def setup_logger(name: str = "senamhi.scheduler") -> logging.Logger:
    """Configure logger for scheduler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
