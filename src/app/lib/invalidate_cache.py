from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.constants import (
    FASTAPI_CACHE_PREFIX,
    USER_AUTH_CACHE_PREFIX,
)

if TYPE_CHECKING:
    from uuid import UUID

    from app.lib.deps import RedisClientDep

USER_AUTH_CACHE_NAMESPACE = f"{FASTAPI_CACHE_PREFIX}:{USER_AUTH_CACHE_PREFIX}"


async def invalidate_user_cache(
    user_id: UUID,
    redis_client: RedisClientDep,
) -> None:
    """Invalidates the cached authentication/authorization data for a user by their ID."""
    cache_key = f"{USER_AUTH_CACHE_NAMESPACE}:{user_id}"

    await redis_client.delete(cache_key)
