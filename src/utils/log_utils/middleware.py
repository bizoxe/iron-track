from __future__ import annotations

import time
from typing import (
    TYPE_CHECKING,
    Any,
    TypedDict,
)

from starlette.responses import JSONResponse
from structlog import get_logger
from uvicorn.protocols.utils import get_path_with_query_string

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from starlette.types import ASGIApp, Receive, Scope, Send


logger = get_logger("_uvicorn")


class AccessInfo(TypedDict, total=False):
    status_code: int
    start_time: float


class StructLogMiddleware:
    """ASGI middleware for structured request logging."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        info = AccessInfo()
        response_started = False

        async def inner_send(message: MutableMapping[str, Any]) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                info["status_code"] = message["status"]
                response_started = True
            await send(message)

        try:
            info["start_time"] = time.perf_counter_ns()
            await self.app(scope, receive, inner_send)
        except Exception as e:  # noqa: BLE001
            await logger.aexception(
                "Unhandled exception in request lifecycle",
                exception_class=e.__class__.__name__,
                http_status=500,
            )
            info["status_code"] = 500
            if not response_started:
                response = JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred.",
                    },
                )
                await response(scope, receive, send)
        finally:
            process_time = (time.perf_counter_ns() - info["start_time"]) / 1_000_000
            client_info = scope.get("client")
            client_host, client_port = client_info if client_info is not None else ("-", 0)
            http_method = scope["method"]
            http_version = scope["http_version"]
            url = get_path_with_query_string(scope)  # type: ignore[arg-type]

            await logger.ainfo(
                "request_completed",
                duration_ms=process_time,
                http={
                    "url": str(url),
                    "status_code": info["status_code"],
                    "method": http_method,
                    "version": http_version,
                },
                network={"client": {"ip": client_host, "port": client_port}},
                path=scope["path"],
                client_ip=client_host,
            )
