"""Enhanced structured logging with request flow tracking.

- Uses standard library `logging`.
- Controlled by env var LOG_LEVEL (default INFO).
- Supports correlation IDs for request flow tracking.
- Safe to import from anywhere.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from functools import lru_cache
from typing import Any, Optional

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def _get_level() -> int:
    level = (os.getenv("LOG_LEVEL") or "INFO").upper()
    return getattr(logging, level, logging.INFO)


class CorrelationIdFilter(logging.Filter):
    """Add correlation_id to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id.get() or "N/A"
        return True


@lru_cache(maxsize=1)
def configure_logging() -> None:
    """Configure logging with console handler to ensure logs are visible."""
    root_logger = logging.getLogger()
    root_logger.setLevel(_get_level())

    # Remove existing handlers to avoid duplicates.
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_get_level())
    console_handler.addFilter(CorrelationIdFilter())

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(correlation_id)s] %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    configure_logging()
    logger = logging.getLogger(name)
    logger.setLevel(_get_level())
    return logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for the current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _correlation_id.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return _correlation_id.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    _correlation_id.set(None)


def kv(**fields: Any) -> str:
    """Render simple key=value pairs for logs."""
    parts = [f"{k}={v!r}" for k, v in fields.items()]
    return " ".join(parts)

