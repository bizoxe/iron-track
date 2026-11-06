from datetime import datetime
from typing import Annotated

from annotated_types import MaxLen, MinLen
from pydantic import Field, field_validator

from app.lib.schema import (
    BaseStruct,
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

__all__ = (
    "CatalogList",
    "CatalogReadBase",
    "EquipmentCreate",
    "EquipmentList",
    "EquipmentRead",
    "EquipmentRestore",
    "EquipmentUpdate",
    "MuscleGroupCreate",
    "MuscleGroupList",
    "MuscleGroupRead",
    "MuscleGroupRestore",
    "MuscleGroupUpdate",
    "TagCreate",
    "TagList",
    "TagRead",
    "TagRestore",
    "TagUpdate",
)


class CatalogReadBase(CamelizedBaseStruct, omit_defaults=True):
    """Base schema for reading catalog items."""

    id: int
    name: str
    deleted_at: datetime | None = None


class CatalogCreateBase(CamelizedBaseSchema):
    """Base schema for creating new catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100)]

    @field_validator("name", mode="before")
    def normalize_name(cls, v: object) -> object:  # noqa: N805
        if isinstance(v, str):
            return " ".join(v.split()).lower()
        return v


class CatalogUpdateBase(CatalogCreateBase):
    """Base schema for updating catalog items."""


class CatalogRestoreBase(CatalogCreateBase):
    """Base schema for restoring catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100), Field(default=None)]


class MuscleGroupRead(CatalogReadBase):
    """Public representation of a muscle group."""


class EquipmentRead(CatalogReadBase):
    """Public representation of a piece of equipment."""


class TagRead(CatalogReadBase):
    """Public representation of an exercise tag."""


class MuscleGroupCreate(CatalogCreateBase):
    """Schema for creating a new muscle group."""


class EquipmentCreate(CatalogCreateBase):
    """Schema for creating a new piece of equipment."""


class TagCreate(CatalogCreateBase):
    """Schema for creating a new exercise tag."""


class MuscleGroupUpdate(CatalogUpdateBase):
    """Schema for updating a muscle group."""


class EquipmentUpdate(CatalogUpdateBase):
    """Schema for updating a piece of equipment."""


class TagUpdate(CatalogUpdateBase):
    """Schema for updating an exercise tag."""


class MuscleGroupRestore(CatalogRestoreBase):
    """Schema for restoring a retired muscle group."""


class EquipmentRestore(CatalogRestoreBase):
    """Schema for restoring a retired piece of equipment."""


class TagRestore(CatalogRestoreBase):
    """Schema for restoring a retired exercise tag."""


class CatalogList[T](BaseStruct):
    """Base envelope for catalog list results."""

    items: list[T]


class EquipmentList(CatalogList[EquipmentRead]):
    """Cache envelope for the equipment list."""


class MuscleGroupList(CatalogList[MuscleGroupRead]):
    """Cache envelope for the muscle group list."""


class TagList(CatalogList[TagRead]):
    """Cache envelope for the tag list."""
