from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from cashews import cache

from app.lib.serializers import MsgSpecRegistry

if TYPE_CHECKING:
    from app.config.base import Settings


def setup_app_cache(settings: Settings) -> None:
    """Configure cache backend and register domain serializers."""
    MsgSpecRegistry.register_in_cashews()
    cache.setup(
        settings_url=settings.cache.URL,
        client_side=True,
        suppress=settings.cache.suppress,
        socket_timeout=0.5,
        # On GET cashews runs the default pickler over registered types' raw
        # b"Type:<msgspec>" bytes and reaches the registered decoder only as a
        # fallback; uncaught pickle errors fail the request. "null" disables the
        # pickler, making MSGSPEC_CACHED_SCHEMAS a required whitelist: an
        # unregistered cached type fails on SET instead of being pickled.
        pickle_type="null",
    )


async def shutdown_app_cache() -> None:
    """Close cache backend connections."""
    with suppress(Exception):  # teardown must not mask the shutdown reason
        await cache.close()
