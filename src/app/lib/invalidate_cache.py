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
    """Invalidate the cached data for a user by ID.

    This function constructs the specific cache key using predefined namespaces
    and deletes the corresponding entry in Redis.

    Args:
        user_id (UUID): The unique identifier of the user.
        redis_client (Redis): An asynchronous Redis client instance.
    """
    cache_key = f"{USER_AUTH_CACHE_NAMESPACE}:{user_id}"

    await redis_client.delete(cache_key)
