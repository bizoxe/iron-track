from typing import Annotated

from fastapi import (
    Depends,
    Request,
)
from redis.asyncio import Redis


async def get_redis_client(request: Request) -> Redis:
    """Dependency for retrieving the Redis client instance."""
    redis_client: Redis = request.app.state.redis_client
    return redis_client


RedisClientDep = Annotated[Redis, Depends(get_redis_client)]
