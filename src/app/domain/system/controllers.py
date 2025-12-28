from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Literal,
    cast,
)

from fastapi import (
    APIRouter,
    status,
)
from redis import RedisError
from sqlalchemy import text
from structlog import get_logger

from app.config.app_settings import DatabaseSession  # noqa: TC001
from app.domain.system import urls
from app.domain.system.schemas import SystemHealth
from app.lib.deps import RedisClientDep  # noqa: TC001
from app.lib.json_response import MsgSpecJSONResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable

system_router = APIRouter(tags=["System"])

logger = get_logger()

OnlineOffline = Literal["online", "offline"]


@system_router.get(
    path=urls.SYSTEM_HEALTH,
    operation_id="SystemHealth",
    name="system:health",
    summary="Health Check",
)
async def check_system_health(
    db_session: DatabaseSession,
    redis_client: RedisClientDep,
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
        cache_ping = await cast("Awaitable[bool]", redis_client.ping())
    except RedisError:
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
