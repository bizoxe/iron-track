from __future__ import annotations

import logging.config
from typing import (
    TYPE_CHECKING,
    Any,
)

import msgspec
import structlog
from asgi_correlation_id import correlation_id

from app.config.base import get_settings
from app.utils.log_utils.handlers import CustomQueueHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

settings = get_settings()


def msgspec_dumps_str(data: Mapping[str, Any], **kwargs: Any) -> str:
    """Serialize a log record dictionary to a JSON string using msgspec."""
    return msgspec.json.encode(data).decode()


def add_correlation(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add request id to log message."""
    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging() -> None:
    """Set up non-blocking, structured logging for the application."""
    shared_processors = [
        add_correlation,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.format_exc_info,
    ]

    processors: list[Any] = [*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter]

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.LEVEL),
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    minimal_pre_chain = [
        add_correlation,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(serializer=msgspec_dumps_str),
                    "foreign_pre_chain": minimal_pre_chain,
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(
                        sort_keys=True,
                        exception_formatter=structlog.dev.plain_traceback,
                    ),
                    "foreign_pre_chain": minimal_pre_chain,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": settings.log.final_formatter,
                },
                "queue_handler": {
                    "class": CustomQueueHandler,
                    "listener": "logging.handlers.QueueListener",
                    "queue": {
                        "()": "queue.Queue",
                        "maxsize": 10000,
                    },
                    "handlers": ["console"],
                    "respect_handler_level": True,
                    "formatter": None,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["queue_handler"],
                    "level": settings.log.LEVEL,
                },
                "app.access": {
                    "propagate": False,
                    "level": settings.log.MIDDLEWARE_LOG_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "uvicorn.error": {
                    "propagate": False,
                    "level": settings.log.UVICORN_ERROR_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "uvicorn.access": {
                    "propagate": False,
                    "level": settings.log.UVICORN_ACCESS_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "sqlalchemy.engine": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_handler"],
                },
            },
        }
    )
