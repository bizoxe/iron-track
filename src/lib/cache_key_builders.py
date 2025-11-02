from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)
from uuid import uuid4

from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import (
        Request,
        Response,
    )

log = get_logger()


def query_params_key_builder(  # noqa: PLR0913
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Request | None = None,
    response: Response | None = None,
    args: Any,
    kwargs: Any,
) -> str:
    """Create a cache key based on the URL path and query parameters.

    Ignores unstable objects (services) and dependencies.
    """
    return f"{namespace}:{request.url.path}:{sorted(request.query_params.items())!r}"  # type: ignore[union-attr]


def user_auth_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *args: Any,
    **kwargs: Any,
) -> str:
    """Create a cache key based on the user ID ('sub') from the token payload.

    Ensures that authentication data is cached uniquely for each user.
    """
    user_id = kwargs.get("kwargs", {}).get("token_payload", {}).get("sub")
    if user_id is not None:
        return f"{namespace}:{user_id}"

    log.error(
        "Cache_Key_Builder_Fallback_Infrastructure_Error",
        message="Internal: Failed to extract 'sub' for cache key. Infrastructure wrapper failure detected. "
        "Forcing DB lookup",
    )
    return f"{namespace}:FORCE_DB_MISS:{uuid4()}"
