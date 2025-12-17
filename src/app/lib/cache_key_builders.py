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
    """Create a cache key based on the URL path and sorted query parameters.

    Ignores unstable objects (services) and dependencies, ensuring a stable
    key derived from the HTTP request context.

    Args:
        func (Callable): The function being cached.
        namespace (str): The namespace defined in the cache decorator.
        request (Request | None): The request object.
        response (Response | None): The response object.
        args (Any): Positional arguments passed to the cached function.
        kwargs (Any): Keyword arguments passed to the cached function.

    Returns:
        str: A unique cache key combining namespace, path, and sorted query parameters.
    """
    return f"{namespace}:{request.url.path}:{sorted(request.query_params.items())!r}"  # type: ignore[union-attr]


def user_auth_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *args: Any,
    **kwargs: Any,
) -> str:
    """Create a cache key based on the user ID ('sub') from the token payload.

    Ensures that authentication data is cached uniquely for each authenticated user.
    Falls back to a unique, non-cached key if the user ID cannot be reliably extracted.

    Args:
        func (Callable): The function being cached.
        namespace (str): The namespace defined in the cache decorator.
        *args (Any): Positional arguments passed to the cached function.
        **kwargs (Any): Keyword arguments passed to the cached function.

    Returns:
        str: A unique cache key based on the user ID, or a unique key forcing a cache miss
             upon failure.
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
