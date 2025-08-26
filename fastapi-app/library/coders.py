from typing import Any

import msgspec
from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder


class MsgSpecJsonCoder(Coder):
    """Custom coder to encode and decode Redis cache results."""

    @classmethod
    def encode(cls, value: Any) -> bytes:
        return msgspec.json.encode(jsonable_encoder(value))

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return msgspec.json.decode(value)
