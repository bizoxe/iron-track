from typing import Literal

from cashews import cache
from cashews.exceptions import CacheBackendInteractionError
from fastapi import (
    APIRouter,
    status,
)
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


@system_router.get(
    path=urls.SYSTEM_HEALTH,
    operation_id="SystemHealth",
    name="system:health",
    summary="Health Check.",
)
async def check_system_health(
    db_session: DatabaseSession,
) -> MsgSpecJSONResponse:
    """Check the health of critical system components.

    Returns:
        MsgSpecJSONResponse: 200 status code if all systems are online, otherwise 503.
    """
    try:
        await db_session.execute(text("SELECT 1"))
        db_ping = True
    except ConnectionRefusedError:
        db_ping = False
    db_status: OnlineOffline = "online" if db_ping else "offline"

    try:
        await cache.ping()
        cache_ping = True
    except (CacheBackendInteractionError, TimeoutError):
        cache_ping = False
    cache_status: OnlineOffline = "online" if cache_ping else "offline"

    healthy = db_ping and cache_ping
    if healthy:
        await logger.adebug(
            "System Health",
            database_status=db_status,
            cache_status=cache_status,
        )
    else:
        await logger.awarn(
            "System Health Check",
            database_status=db_status,
            cache_status=cache_status,
        )

    return MsgSpecJSONResponse(
        content=SystemHealth(database_status=db_status, cache_status=cache_status),
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@system_router.get(
    path=urls.SYSTEM_PING,
    operation_id="SystemPing",
    name="system:ping",
    summary="Ping Check.",
)
def ping() -> PlainTextResponse:
    """Check the health status of the application.

    Returns:
        PlainTextResponse: A plain text response "OK" to confirm the server is reachable.
    """
    return PlainTextResponse(content=b"OK")
