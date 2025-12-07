from collections.abc import Mapping
from typing import Any

from fastapi import Response
from fastapi.encoders import jsonable_encoder
from msgspec import json as mjson
from starlette.background import BackgroundTask

_JSON_ENCODER = mjson.Encoder()


class MsgSpecJSONResponse(Response):
    """JSON response using the high-performance `msgspec` library to serialize data to JSON."""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str = "application/json",
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: Any) -> bytes:
        return _JSON_ENCODER.encode(jsonable_encoder(content))
