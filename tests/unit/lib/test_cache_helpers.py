from typing import TYPE_CHECKING

import pytest

from app.config.constants import (
    FASTAPI_CACHE_PREFIX,
    USER_AUTH_CACHE_PREFIX,
)
from app.lib.invalidate_cache import invalidate_user_cache
from tests.constants import USER_EXAMPLE_ID

if TYPE_CHECKING:
    from redis.asyncio import Redis


pytestmark = pytest.mark.anyio

CACHE_NAMESPACE = f"{FASTAPI_CACHE_PREFIX}:{USER_AUTH_CACHE_PREFIX}"


async def test_invalidate_user_cache(
    redis_client: "Redis",
) -> None:
    cache_key = f"{CACHE_NAMESPACE}:{USER_EXAMPLE_ID}"
    await redis_client.set(name=cache_key, value="1")
    assert await redis_client.exists(cache_key) == 1
    await invalidate_user_cache(
        user_id=USER_EXAMPLE_ID,
        redis_client=redis_client,
    )
    assert await redis_client.exists(cache_key) == 0
