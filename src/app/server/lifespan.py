from __future__ import annotations

from typing import TYPE_CHECKING

from cashews import cache

from app.lib.serializers import cashews_registry

if TYPE_CHECKING:
    from app.config.base import Settings


def setup_app_cache(settings: Settings) -> None:
    """Configure cache backend and bind domain serializers."""
    cashews_registry()
    cache.setup(
        settings_url=settings.redis.URL,
        client_side=True,
        suppress=False,
        socket_timeout=0.5,
    )
