from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder
from msgspec import json as mjson

_JSON_ENCODER = mjson.Encoder()
_JSON_DECODER = mjson.Decoder(Any)


class MsgSpecJsonCoder(Coder):
    """Custom coder to encode and decode Redis cache results."""

    @classmethod
    def encode(cls, value: Any) -> bytes:
        return _JSON_ENCODER.encode(jsonable_encoder(value))

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return _JSON_DECODER.decode(value)
