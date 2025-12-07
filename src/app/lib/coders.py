from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder
from msgspec import msgpack

from app.domain.users.schemas import UserAuth


class MsgPackCoderBase(Coder):
    """Base coder to encode and decode Redis cache results."""

    _MSGPACK_ENCODER = msgpack.Encoder()
    _MSGPACK_DECODER_DICT = msgpack.Decoder(dict)

    @classmethod
    def encode(cls, value: Any) -> bytes:
        return cls._MSGPACK_ENCODER.encode(jsonable_encoder(value))

    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError


class MsgPackCoder(MsgPackCoderBase):
    @classmethod
    def decode(cls, value: bytes) -> dict[str, Any]:
        return cls._MSGPACK_DECODER_DICT.decode(value)


class MsgPackCoderUserAuth(MsgPackCoderBase):
    @classmethod
    def decode(cls, value: bytes) -> UserAuth:
        raw_data = cls._MSGPACK_DECODER_DICT.decode(value)
        return UserAuth.model_validate(raw_data)
