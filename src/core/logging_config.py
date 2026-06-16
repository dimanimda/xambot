"""Structured logging configuration with structlog.

Supports JSON (production) and console (development) output formats.
"""

import logging
import structlog
from src.core.config import settings


def setup_logging() -> None:
    """Configure structlog with the chosen format and log level."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.log_format == "json":
        structlog.configure(
            processors=shared_processors + [structlog.processors.JSONRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.log_level)
            ),
        )
    else:
        structlog.configure(
            processors=shared_processors + [structlog.dev.ConsoleRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.log_level)
            ),
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a structlog logger for the given module name."""
    return structlog.get_logger(name)
