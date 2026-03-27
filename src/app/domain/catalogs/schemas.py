from typing import Annotated

from annotated_types import (
    MaxLen,
    MinLen,
)
from pydantic import field_validator

from app.lib.schema import (
    CamelizedBaseSchema,
    CamelizedBaseStruct,
)

__all__ = (
    "EquipmentCreate",
    "EquipmentRead",
    "EquipmentUpdate",
    "ExerciseTagCreate",
    "ExerciseTagRead",
    "ExerciseTagUpdate",
    "FieldsReadBase",
    "MuscleGroupCreate",
    "MuscleGroupRead",
    "MuscleGroupUpdate",
)


class FieldsReadBase(CamelizedBaseStruct):
    """Base schema for reading catalog items."""

    id: int
    name: str


class FieldsCreateBase(CamelizedBaseSchema):
    """Base schema for creating new catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100)]

    @field_validator("name", mode="after")
    def normalize_name(cls, v: str) -> str:  # noqa: N805
        return " ".join(v.split()).lower()


class FieldsUpdateBase(FieldsCreateBase):
    """Base schema for updating catalog items."""

    name: Annotated[str, MinLen(3), MaxLen(100)]


class MuscleGroupCreate(FieldsCreateBase):
    """Schema for creating a new muscle group.

    Example: 'chest', 'biceps'.
    """


class EquipmentCreate(FieldsCreateBase):
    """Schema for creating a new piece of equipment.

    Example: 'barbell', 'kettlebells'.
    """


class ExerciseTagCreate(FieldsCreateBase):
    """Schema for creating a new exercise tag.

    Example: 'mobility', 'isometric'.
    """


class MuscleGroupRead(FieldsReadBase):
    """Public representation of a muscle group."""


class EquipmentRead(FieldsReadBase):
    """Public representation of a piece of equipment."""


class ExerciseTagRead(FieldsReadBase):
    """Public representation of an exercise tag."""


class MuscleGroupUpdate(FieldsUpdateBase):
    """Schema for updating a muscle group."""


class EquipmentUpdate(FieldsUpdateBase):
    """Schema for updating a piece of equipment."""


class ExerciseTagUpdate(FieldsUpdateBase):
    """Schema for updating an exercise tag."""
