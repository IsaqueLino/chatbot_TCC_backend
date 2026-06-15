"""
Logger configuration (Singleton Pattern).

This module provides centralized logging using Python's logging module.
Follows Singleton pattern to ensure consistent logging across application.

Architecture:
- Part of Infrastructure Layer
- Used by all layers for logging
"""

import json
import logging
import sys
from functools import lru_cache
from typing import Any

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields passed via `extra=` in logger calls.
        # The logging module adds those keys into the record's __dict__.
        standard_keys = {
            'name','msg','args','levelname','levelno','pathname','filename','module',
            'exc_info','exc_text','stack_info','lineno','funcName','created','msecs',
            'relativeCreated','thread','threadName','processName','process'
        }
        for k, v in record.__dict__.items():
            if k not in standard_keys and k not in log_data:
                try:
                    log_data[k] = v
                except Exception:
                    log_data[k] = str(v)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logging."""

    def __init__(self) -> None:
        """Initialize text formatter."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


@lru_cache
def get_logger(name: str = "app") -> logging.Logger:
    """Get logger instance (Singleton per name).

    Uses @lru_cache to ensure single logger instance per name.
    This follows Singleton pattern for logging.

    Args:
        name: Logger name (usually module name)

    Returns:
        Logger instance (singleton per name)
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Set log level
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Set formatter based on configuration
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# The `log_extra` helper was removed. Call `logger.<level>(msg, extra={...})` directly.


# Export default logger
logger = get_logger("app")
