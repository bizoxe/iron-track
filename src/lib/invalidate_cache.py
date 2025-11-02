from uuid import UUID

from fastapi_cache import FastAPICache


async def invalidate_user_cache(user_id: UUID) -> None:
    """Invalidates the cached authentication/authorization data for a user by their ID."""
    cache_key = f"user_auth:{user_id}"

    await FastAPICache.clear(cache_key)
