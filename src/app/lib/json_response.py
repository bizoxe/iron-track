from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from fastapi import Response
from msgspec import json as mjson

if TYPE_CHECKING:
    from collections.abc import Mapping

    from starlette.background import BackgroundTask


class MsgSpecJSONResponse(Response):
    """High-performance JSON response using `msgspec` for serialization."""

    encoder: ClassVar[mjson.Encoder] = mjson.Encoder()

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str = "application/json",
        background: BackgroundTask | None = None,
    ) -> None:
        """Initialize the custom response class.

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

        Args:
            content: The data to serialize.

        Returns:
            bytes: Serialized JSON content as bytes.
        """
        return self.encoder.encode(content)
