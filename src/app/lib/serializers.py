from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from cashews.serialize import DecodeError as CashewsDecodeError
from cashews.serialize import register_type
from msgspec import DecodeError, msgpack

from app.domain.accounts.schemas import UserAuth, UserPage
from app.domain.catalogs.schemas import EquipmentList, MuscleGroupList, TagList
from app.domain.exercises.schemas import ExercisePage

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

MSGSPEC_CACHED_SCHEMAS = (
    UserAuth,
    UserPage,
    ExercisePage,
    EquipmentList,
    MuscleGroupList,
    TagList,
)


class MsgSpecRegistry:
    """Domain types serialized with msgspec inside the `cashews` registry."""

    encoder: ClassVar[msgpack.Encoder] = msgpack.Encoder()

    @classmethod
    def register_in_cashews(cls) -> None:
        """Register the cached domain schemas with cashews."""
        for model_type in MSGSPEC_CACHED_SCHEMAS:
            encoder, decoder = cls._get_cashews_pair(model_type)
            register_type(klass=model_type, encoder=encoder, decoder=decoder)

    @classmethod
    def _get_cashews_pair(
        cls,
        target_type: Any,
    ) -> tuple[
        Callable[..., Awaitable[bytes]],
        Callable[..., Awaitable[Any]],
    ]:
        """Create an asynchronous encoder/decoder pair for a specific type."""
        decoder = msgpack.Decoder(target_type)

        async def encode(value: Any, *args: Any, **kwargs: Any) -> bytes:
            return cls.encoder.encode(value)

        async def decode(value: bytes, *args: Any, **kwargs: Any) -> Any:
            try:
                return decoder.decode(value)
            except DecodeError as exc:
                raise CashewsDecodeError from exc

        return encode, decode
