from __future__ import annotations

from typing import TYPE_CHECKING

from cashews import cache

from app.lib.serializers import cashews_registry

if TYPE_CHECKING:
    from app.config.base import Settings


def setup_app_cache(settings: Settings) -> None:
    """Initialize application cache with Redis and msgspec registry.

    Register domain models for serialization and setup cashews backend
    with client-side caching enabled.
    """
    cashews_registry()
    cache.setup(
        settings_url=settings.redis.URL,
        client_side=True,
        suppress=False,
        socket_timeout=0.5,
    )
