from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from cashews.serialize import register_type
from msgspec import msgpack

from app.domain.users.schemas import UserAuth

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class MsgSpecRegistry:
    """Registry for msgspec-based serialization."""

    _ENCODER = msgpack.Encoder()
    """Internal msgpack encoder instance."""

    @classmethod
    def get_cashews_pair(
        cls,
        target_type: Any,
    ) -> tuple[
        Callable[[Any, Any, Any], Awaitable[bytes]],
        Callable[[bytes, Any, Any], Awaitable[Any]],
    ]:
        """Create an asynchronous encoder/decoder pair for a specific type."""
        decoder = msgpack.Decoder(target_type)

        async def _enc(value: Any, *args: Any, **kwargs: Any) -> bytes:
            """Encode a value to msgpack bytes."""
            return cls._ENCODER.encode(value)

        async def _dec(value: bytes, *args: Any, **kwargs: Any) -> Any:
            """Decode msgpack bytes back to the target type."""
            return decoder.decode(value)

        return _enc, _dec


def cashews_registry() -> None:
    """Register domain data models with the cashews serialization system."""
    types_to_register = (UserAuth,)
    for model_type in types_to_register:
        encoder, decoder = MsgSpecRegistry.get_cashews_pair(model_type)
        register_type(klass=model_type, encoder=encoder, decoder=decoder)
