from typing import TYPE_CHECKING

from cashews import cache

if TYPE_CHECKING:
    from uuid import UUID


async def invalidate_user_cache(
    user_id: "UUID",
) -> None:
    """Invalidate the cached data for a user by ID."""
    await cache.delete(key=f"user_auth:{user_id}")
