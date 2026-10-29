"""System Endpoints."""

from typing import Literal

from cashews import cache
from cashews.exceptions import CacheBackendInteractionError
from fastapi import APIRouter, status
from sqlalchemy import text
from starlette.responses import PlainTextResponse
from structlog import get_logger

from app.config.app_settings import DatabaseSession
from app.domain.system import urls
from app.domain.system.schemas import SystemHealth
from app.lib.json_response import MsgSpecJSONResponse

OnlineOffline = Literal["online", "offline"]

logger = get_logger()

system_router = APIRouter(tags=["System"])


SYSTEM_HEALTH_SCHEMA = {
    "type": "object",
    "properties": {
        "database_status": {
            "type": "string",
            "enum": ["online", "offline"],
        },
        "cache_status": {
            "type": "string",
            "enum": ["online", "offline"],
        },
        "app": {"type": "string"},
        "version": {"type": "string"},
    },
    "required": [
        "database_status",
        "cache_status",
        "app",
        "version",
    ],
}


@system_router.get(
    path=urls.SYSTEM_HEALTH,
    operation_id="CheckSystemHealth",
    name="system:health",
    summary="Check system health",
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "schema": SYSTEM_HEALTH_SCHEMA,
                },
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "content": {
                "application/json": {
                    "schema": SYSTEM_HEALTH_SCHEMA,
                },
            },
        },
    },
)
async def check_system_health(
    db_session: DatabaseSession,
) -> MsgSpecJSONResponse:
    """Check the health of critical system components."""
    db_error: str | None = None
    try:
        await db_session.execute(text("SELECT 1"))
        db_ping = True
    except Exception as exc:  # noqa: BLE001 — health probe: report, don't crash
        db_ping = False
        db_error = repr(exc)
    db_status: OnlineOffline = "online" if db_ping else "offline"

    cache_error: str | None = None
    try:
        await cache.ping()
        cache_ping = True
    except (CacheBackendInteractionError, TimeoutError) as exc:
        # deliberately narrow: cashews wraps every backend failure into this contract
        cache_ping = False
        cache_error = repr(exc) if exc.__cause__ is None else f"{exc!r} (cause: {exc.__cause__!r})"
    cache_status: OnlineOffline = "online" if cache_ping else "offline"

    healthy = db_ping and cache_ping
    if healthy:
        logger.debug(
            "System Health Check",
            database_status=db_status,
            cache_status=cache_status,
        )
    else:
        logger.warning(
            "System Health Check",
            database_status=db_status,
            cache_status=cache_status,
            database_error=db_error,
            cache_error=cache_error,
        )

    return MsgSpecJSONResponse(
        content=SystemHealth(database_status=db_status, cache_status=cache_status),
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@system_router.get(
    path=urls.PING,
    operation_id="Ping",
    name="system:ping",
    summary="Ping the application",
    response_class=PlainTextResponse,
)
def ping() -> PlainTextResponse:
    """Confirm that the server is reachable."""
    return PlainTextResponse(content=b"OK")
