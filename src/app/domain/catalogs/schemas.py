from datetime import datetime
from typing import Annotated

from annotated_types import MaxLen, MinLen
from pydantic import Field, field_validator

from app.lib.schema import (
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

__all__ = (
    "EquipmentCreate",
    "EquipmentRead",
    "EquipmentRestore",
    "EquipmentUpdate",
    "FieldsReadBase",
    "MuscleGroupCreate",
    "MuscleGroupRead",
    "MuscleGroupRestore",
    "MuscleGroupUpdate",
    "TagCreate",
    "TagRead",
    "TagRestore",
    "TagUpdate",
)


class FieldsReadBase(CamelizedBaseStruct, omit_defaults=True):
    """Base schema for reading catalog items."""

    id: int
    name: str
    deleted_at: datetime | None = None


class FieldsCreateBase(CamelizedBaseSchema):
    """Base schema for creating new catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100)]

    @field_validator("name", mode="before")
    def normalize_name(cls, v: object) -> object:  # noqa: N805
        if isinstance(v, str):
            return " ".join(v.split()).lower()
        return v


class FieldsUpdateBase(FieldsCreateBase):
    """Base schema for updating catalog items."""


class FieldsRestoreBase(FieldsCreateBase):
    """Base schema for restoring catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100), Field(default=None)]


class MuscleGroupRead(FieldsReadBase):
    """Public representation of a muscle group."""


class EquipmentRead(FieldsReadBase):
    """Public representation of a piece of equipment."""


class TagRead(FieldsReadBase):
    """Public representation of an exercise tag."""


class MuscleGroupCreate(FieldsCreateBase):
    """Schema for creating a new muscle group."""


class EquipmentCreate(FieldsCreateBase):
    """Schema for creating a new piece of equipment."""


class TagCreate(FieldsCreateBase):
    """Schema for creating a new exercise tag."""


class MuscleGroupUpdate(FieldsUpdateBase):
    """Schema for updating a muscle group."""


class EquipmentUpdate(FieldsUpdateBase):
    """Schema for updating a piece of equipment."""


class TagUpdate(FieldsUpdateBase):
    """Schema for updating an exercise tag."""


class MuscleGroupRestore(FieldsRestoreBase):
    """Schema for restoring a retired muscle group."""


class EquipmentRestore(FieldsRestoreBase):
    """Schema for restoring a retired piece of equipment."""


class TagRestore(FieldsRestoreBase):
    """Schema for restoring a retired exercise tag."""
