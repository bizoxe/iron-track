from __future__ import annotations

import time
from typing import (
    TYPE_CHECKING,
    Any,
    TypedDict,
)

from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from starlette.types import ASGIApp, Receive, Scope, Send


EXCLUDED_LOG_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }
)

logger = get_logger("app.access")


class AccessInfo(TypedDict, total=False):
    status_code: int
    start_time: int


class StructLogMiddleware:
    """ASGI middleware for structured request logging."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:  # noqa: C901
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        info = AccessInfo(status_code=200)

        async def inner_send(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                info["status_code"] = message["status"]
            await send(message)

        try:
            info["start_time"] = time.perf_counter_ns()
            await self.app(scope, receive, inner_send)
        except Exception:
            logger.exception(
                "Unhandled exception in request lifecycle",
                http_status=500,
            )
            info["status_code"] = 500
            raise
        finally:
            path = scope["path"]
            if path not in EXCLUDED_LOG_PATHS:
                process_time = (time.perf_counter_ns() - info["start_time"]) / 1_000_000
                client_ip = "-"
                for k, v in scope["headers"]:
                    if k == b"x-real-ip":
                        client_ip = v.decode()
                        break
                    if k == b"x-forwarded-for":
                        client_ip = v.decode().split(",")[0].strip()
                        break
                else:
                    client_info = scope.get("client")
                    if client_info:
                        client_ip = client_info[0]

                logger.info(
                    "request_completed",
                    duration_ms=process_time,
                    status_code=info["status_code"],
                    method=scope["method"],
                    path=path,
                    query=scope.get("query_string", b"").decode() or None,
                    client_ip=client_ip,
                )
