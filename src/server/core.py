import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from utils.log_utils.middleware import StructLogMiddleware
from utils.log_utils.setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    queue_handler = logging.getHandlerByName("queue_handler")
    queue_handler.listener.start()  # type: ignore[union-attr]

    yield
    queue_handler.listener.stop()  # type: ignore[union-attr]


def create_app() -> FastAPI:
    _app = FastAPI(lifespan=lifespan)

    _app.add_middleware(StructLogMiddleware)
    _app.add_middleware(CorrelationIdMiddleware)

    return _app
