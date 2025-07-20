import logging.config
from typing import Any

import structlog
from asgi_correlation_id import correlation_id

from config.base import get_settings
from utils.log_utils.handlers import CustomQueueHandler

settings = get_settings()


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
    log_dir = settings.log.LOG_DIR
    log_dir.mkdir(exist_ok=True)

    shared_processors = [
        add_correlation,
        structlog.contextvars.merge_contextvars,
        structlog.threadlocal.merge_threadlocal,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog_only_processors = [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    processors: list[Any] = shared_processors + structlog_only_processors

    structlog.configure(
        processors=processors,
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json_formatter": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": shared_processors + [structlog.processors.format_exc_info],
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(sort_keys=True),
                    "foreign_pre_chain": shared_processors,
                },
                "key_value": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.KeyValueRenderer(
                        key_order=["timestamp", "level", "event", "logger"]
                    ),
                    "foreign_pre_chain": shared_processors + [structlog.processors.format_exc_info],
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "plain_console",
                },
                "json_file": {
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": log_dir.joinpath("log_file.jsonl"),
                    "formatter": "json_formatter",
                    "mode": "a",
                    "encoding": "utf-8",
                },
                "flat_line_file": {
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": log_dir.joinpath("flat_line.jsonl"),
                    "formatter": "key_value",
                    "mode": "a",
                    "encoding": "utf-8",
                },
                "queue_handler": {
                    "class": CustomQueueHandler,
                    "listener": "logging.handlers.QueueListener",
                    "queue": {
                        "()": "queue.Queue",
                        "maxsize": -1,
                    },
                    "handlers": ["console", "json_file", "flat_line_file"],
                    "respect_handler_level": True,
                    "formatter": None,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["queue_handler"],
                    "level": settings.log.LEVEL,
                },
                "_uvicorn": {
                    "propagate": False,
                    "level": settings.log.LEVEL,
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
