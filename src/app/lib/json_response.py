from collections.abc import Mapping
from typing import Any

from fastapi import Response
from fastapi.encoders import jsonable_encoder
from msgspec import json as mjson
from starlette.background import BackgroundTask

_JSON_ENCODER = mjson.Encoder()


class MsgSpecJSONResponse(Response):
    """High-performance JSON response using `msgspec` for serialization."""

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str = "application/json",
        background: BackgroundTask | None = None,
    ) -> None:
        """Initializes the custom response class.

        Args:
            content: The content to be serialized.
            status_code (int): HTTP status code.
            headers (Mapping[str, str] | None): HTTP headers.
            media_type (str): Media type (default: application/json).
            background (BackgroundTask | None): Background task to run after the response is sent.
        """
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: Any) -> bytes:
        """Serialize the content using the `msgspec` encoder.

        The content is first passed through `fastapi.encoders.jsonable_encoder`
        to handle standard FastAPI types (e.g., Pydantic models).

        Args:
            content: The data to serialize.

        Returns:
            bytes: Serialized JSON content as bytes.
        """
        return _JSON_ENCODER.encode(jsonable_encoder(content))
