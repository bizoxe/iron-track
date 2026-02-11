import msgspec
from advanced_alchemy.utils.text import camelize
from pydantic import BaseModel as BaseSchema
from pydantic import ConfigDict


class BaseStruct(msgspec.Struct):
    """Base msgspec structure for API responses."""


class CamelizedBaseStruct(BaseStruct, rename="camel"):
    """Camelized base msgspec structure for frontend responses."""


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=camelize,
        extra="forbid",
        use_enum_values=True,
        from_attributes=False,
        frozen=True,
    )
