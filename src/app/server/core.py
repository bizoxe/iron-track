from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from msgspec import json as mjson
from pydantic import TypeAdapter

from app.__about__ import __version__ as current_version
from app.config.app_settings import alchemy
from app.config.base import get_settings
from app.db.soft_delete import register_soft_delete_filter
from app.domain.accounts.controllers.access import access_router
from app.domain.accounts.controllers.user_roles import user_roles_router
from app.domain.accounts.controllers.users import users_router
from app.domain.catalogs.controllers.equipment import equipment_router
from app.domain.catalogs.controllers.exercise_tags import exercise_tags_router
from app.domain.catalogs.controllers.muscle_groups import muscle_groups_router
from app.domain.exercises.controllers import exercises_router
from app.domain.system.controllers import system_router
from app.lib.exceptions import BaseAPIException
from app.lib.handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from app.lib.schema import ValidationErrorSchema
from app.server.cache import setup_app_cache, shutdown_app_cache
from app.server.observability.middleware import StructLogMiddleware
from app.server.observability.setup import (
    configure_logging,
    start_logging,
    stop_logging,
)
from app.server.openapi import MSGSPEC_SCHEMAS

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.config.base import Settings


@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings) -> AsyncIterator[None]:
    start_logging()
    setup_app_cache(settings=settings)
    try:
        yield
    finally:
        await shutdown_app_cache()
        stop_logging()


def custom_openapi(app: FastAPI) -> None:
    """Generate and customize the application OpenAPI schema."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schemas_registry = openapi_schema.setdefault("components", {}).setdefault("schemas", {})

    ta = TypeAdapter(ValidationErrorSchema)
    json_schema = ta.json_schema(ref_template="#/components/schemas/{model}")
    defs = json_schema.pop("$defs", {})
    schemas_registry.update(defs)
    schemas_registry["ValidationErrorSchema"] = json_schema

    validation_error_ref = {"$ref": "#/components/schemas/ValidationErrorSchema"}
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "422" in method["responses"]:
                method["responses"]["422"]["content"]["application/json"]["schema"] = validation_error_ref
    schemas_registry.pop("ValidationError", None)
    schemas_registry.pop("HTTPValidationError", None)

    _, components = mjson.schema_components(MSGSPEC_SCHEMAS, ref_template="#/components/schemas/{name}")
    schemas_registry.update(components)

    app.openapi_schema = openapi_schema


def init_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""
    app.add_exception_handler(BaseAPIException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]


def init_routers(app: FastAPI, settings: Settings) -> None:
    """Include all domain-specific routers into the application."""
    app.include_router(access_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(user_roles_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(users_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(equipment_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(exercise_tags_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(muscle_groups_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(exercises_router, prefix=settings.app.API_V1_URL_PREFIX)
    app.include_router(system_router)


def create_app() -> FastAPI:
    """Create and configure the core FastAPI application instance."""
    settings = get_settings()
    configure_logging()
    app = FastAPI(
        debug=settings.app.DEBUG,
        title=settings.app.NAME,
        version=current_version,
        description=(
            "Experimental async backend sandbox built for architectural exploration and performance analysis\n\n"
            "Focused on concurrency patterns, database optimization, and constraint-driven experiments within a workout"
            " tracking domain."
        ),
        lifespan=lambda app: lifespan(app, settings=settings),
        docs_url="/docs" if settings.app.ENVIRONMENT == "dev" else None,
        redoc_url="/redoc" if settings.app.ENVIRONMENT == "dev" else None,
        openapi_url="/openapi.json" if settings.app.ENVIRONMENT == "dev" else None,
    )
    alchemy.init_app(app)
    register_soft_delete_filter()
    init_routers(app=app, settings=settings)
    init_error_handlers(app=app)
    app.add_middleware(StructLogMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    custom_openapi(app)

    return app
