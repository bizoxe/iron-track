import pytest
from cashews import cache as cashews_cache

from app.lib.invalidate_cache import invalidate_user_cache
from tests.constants import USER_EXAMPLE_ID

pytestmark = pytest.mark.anyio


async def test_invalidate_user_cache() -> None:
    cache_key = f"user_auth:{USER_EXAMPLE_ID}"
    await cashews_cache.set(key=cache_key, value="1")
    assert await cashews_cache.exists(key=cache_key) is True
    await invalidate_user_cache(
        user_id=USER_EXAMPLE_ID,
    )
    assert await cashews_cache.exists(key=cache_key) is False
