"""DB binding of the domain vocabulary: physical enum names, DDL, column types."""

import re
from enum import StrEnum
from typing import Final

from sqlalchemy.dialects import postgresql as pg

from app.domain.enums import (
    Category,
    DifficultyLevel,
    Force,
    Mechanic,
    MuscleRole,
    SessionStatus,
    SharingStatus,
    UnitExerciseMode,
)

DB_ENUMS: Final[tuple[type[StrEnum], ...]] = (
    Category,
    DifficultyLevel,
    Force,
    Mechanic,
    MuscleRole,
    SessionStatus,
    SharingStatus,
    UnitExerciseMode,
)


def to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def enum_type_name(enum_cls: type[StrEnum]) -> str:
    """Return the PostgreSQL enum type name."""
    return f"{to_snake(enum_cls.__name__)}_enum"


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    """values_callable for pg.ENUM: persist .value labels, not member names."""
    return [member.value for member in enum_cls]


def pg_enum[E: StrEnum](cls: type[E]) -> pg.ENUM:
    """Return a PostgreSQL enum column type without creating the database type."""
    return pg.ENUM(cls, name=enum_type_name(cls), create_type=False, values_callable=enum_values)
