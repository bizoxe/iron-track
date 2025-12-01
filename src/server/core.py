from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.config.app_settings import alchemy
from src.config.base import get_settings
from src.config.constants import FASTAPI_CACHE_PREFIX
from src.domain.users.controllers.access import access_router
from src.domain.users.controllers.user_role import role_router
from src.domain.users.controllers.users import users_router
from src.lib.exceptions import BaseAPIException
from src.lib.handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from src.utils.log_utils.middleware import StructLogMiddleware
from src.utils.log_utils.setup import configure_logging

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.config.base import Settings


@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings) -> AsyncIterator[None]:
    configure_logging()
    queue_handler = logging.getHandlerByName("queue_handler")
    queue_handler.listener.start()  # type: ignore[union-attr]

    redis_client = settings.redis.client
    FastAPICache.init(RedisBackend(redis_client), prefix=FASTAPI_CACHE_PREFIX)
    app.state.redis_client = redis_client

    yield
    await redis_client.aclose()
    queue_handler.listener.stop()  # type: ignore[union-attr]


def _init_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BaseAPIException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]


def _init_routers(app: FastAPI, settings: Settings) -> None:
    app.include_router(access_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(users_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(role_router, prefix=settings.app.API_V1_URL_PREFIX)


def create_app() -> FastAPI:
    settings = get_settings()
    _app = FastAPI(lifespan=lambda app: lifespan(app, settings=settings))
    alchemy.init_app(_app)
    _init_routers(app=_app, settings=settings)
    _init_error_handlers(app=_app)
    _app.add_middleware(StructLogMiddleware)
    _app.add_middleware(CorrelationIdMiddleware)

    return _app
