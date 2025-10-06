"""Structured logging setup utilities."""

from typing import Any, Dict

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog with JSON output suitable for distributed tracing."""

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(structlog.logging, level, 20)),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def build_logger(name: str, **context: Dict[str, Any]) -> structlog.stdlib.BoundLogger:
    """Create a structlog bound logger with default context."""

    logger = structlog.get_logger(name)
    if context:
        return logger.bind(**context)
    return logger
