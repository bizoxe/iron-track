from __future__ import annotations

import time
from typing import (
    TYPE_CHECKING,
    Any,
    TypedDict,
)

import structlog
from starlette.responses import JSONResponse
from uvicorn.protocols.utils import get_path_with_query_string

from config.base import get_settings

settings = get_settings()

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from starlette.types import ASGIApp, Receive, Scope, Send


logger = structlog.stdlib.get_logger("_uvicorn")


class AccessInfo(TypedDict, total=False):
    status_code: int
    start_time: float


class StructLogMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        info = AccessInfo()

        async def inner_send(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                info["status_code"] = message["status"]
            await send(message)

        try:
            info["start_time"] = time.perf_counter_ns()
            await self.app(scope, receive, inner_send)
        except Exception as e:
            await logger.aexception(
                "An unhandled exception was caught by last resort middleware",
                exception_class=e.__class__.__name__,
                exc_info=e,
            )
            info["status_code"] = 500
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
            client_host, client_port = scope["client"]
            http_method = scope["method"]
            http_version = scope["http_version"]
            url = get_path_with_query_string(scope)  # type: ignore

            await logger.ainfo(
                f"""{client_host}:{client_port} - "{http_method} {scope["path"]} HTTP/{http_version}" {info["status_code"]}""",
                http={
                    "url": str(url),
                    "status_code": info["status_code"],
                    "method": http_method,
                    "version": http_version,
                },
                network={"client": {"ip": client_host, "port": client_port}},
                duration_ms=process_time,
            )
