from __future__ import annotations

import logging
import logging.config
import logging.handlers
from datetime import UTC, datetime
from queue import Queue
from typing import TYPE_CHECKING, Any, cast

import structlog
from asgi_correlation_id import correlation_id
from msgspec import json as mjson

from app.config.base import get_settings

if TYPE_CHECKING:
    from collections.abc import Mapping

    from structlog.typing import EventDict, WrappedLogger

settings = get_settings()

json_encoder = mjson.Encoder()

log_queue: Queue[logging.LogRecord] = Queue(10000)
log_listener: logging.handlers.QueueListener | None = None


def msgspec_dumps_str(data: Mapping[str, Any], **kwargs: Any) -> str:
    """Serialize a log record dictionary to a JSON string using `msgspec`."""
    return json_encoder.encode(data).decode()


def add_correlation(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add request id to log message."""
    if request_id := correlation_id.get():
        event_dict["request_id"] = request_id
    return event_dict


def add_request_id(logger: WrappedLogger, name: str, event_dict: EventDict) -> EventDict:
    """Attach the request id captured by CustomQueueHandler at queuing time."""
    record = event_dict.get("_record")
    if (request_id := getattr(record, "request_id", None)) is not None:
        event_dict["request_id"] = request_id
    return event_dict


def stamp_from_record(logger: WrappedLogger, name: str, event_dict: EventDict) -> EventDict:
    """Stamp records with their creation time, not listener format time."""
    record = event_dict.get("_record")
    if record is not None:
        event_dict["timestamp"] = datetime.fromtimestamp(record.created, tz=UTC).isoformat().replace("+00:00", "Z")
    return event_dict


def configure_logging() -> None:
    """Set up non-blocking, structured logging for the application."""
    shared_processors = [
        add_correlation,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ]

    processors: list[Any] = [*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter]

    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.STRUCTLOG_LEVEL),
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    minimal_pre_chain = [
        add_request_id,
        stamp_from_record,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "json_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.processors.format_exc_info,
                        structlog.processors.JSONRenderer(serializer=msgspec_dumps_str),
                    ],
                    "foreign_pre_chain": minimal_pre_chain,
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.dev.ConsoleRenderer(
                            sort_keys=True,
                            exception_formatter=structlog.dev.plain_traceback,
                        ),
                    ],
                    "foreign_pre_chain": minimal_pre_chain,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": settings.log.final_formatter,
                },
                "queue_handler": {
                    "class": "app.server.observability.handlers.CustomQueueHandler",
                    "queue": log_queue,
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
                    "level": settings.log.ASGI_ERROR_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "uvicorn.access": {
                    "propagate": False,
                    "level": settings.log.ASGI_ACCESS_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "sqlalchemy.engine.Engine": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "_granian": {
                    "propagate": False,
                    "level": settings.log.ASGI_ERROR_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "granian.access": {
                    "propagate": False,
                    "level": settings.log.ASGI_ACCESS_LEVEL,
                    "handlers": ["queue_handler"],
                },
                "cashews": {
                    "level": settings.log.CASHEWS_LEVEL,
                },
            },
        }
    )
    console_handler = cast("logging.StreamHandler[Any]", logging.getHandlerByName("console"))
    global log_listener  # noqa: PLW0603
    log_listener = logging.handlers.QueueListener(log_queue, console_handler)


def start_logging() -> None:
    """Start the background log listener (called from the app lifespan)."""
    if log_listener:
        log_listener.start()


def stop_logging() -> None:
    """Stop the background log listener (called on app lifespan shutdown)."""
    if log_listener:
        log_listener.stop()
