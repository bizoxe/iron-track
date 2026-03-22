from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.domain.exercises.schemas import (
    CategoryType,
    DifficultyLevelType,
    ForceType,
    MechanicType,
)

from .reference import (
    exercise_equipment,
    exercise_primary_muscles,
    exercise_secondary_muscles,
    exercise_tag_map,
)

if TYPE_CHECKING:
    from .reference import Equipment, ExerciseTag, MuscleGroup


class Exercise(UUIDv7AuditBase):
    """Represents a physical exercise and its biomechanical properties."""

    __tablename__ = "exercises"

    name: Mapped[str] = mapped_column(String(100), nullable=True)
    """The display name of the exercise."""
    force: Mapped[ForceType] = mapped_column(
        pg.ENUM(
            ForceType,
            name="force_enum",
            create_type=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=True,
    )
    """Type of force applied (pull, push, static)."""
    difficulty_level: Mapped[DifficultyLevelType] = mapped_column(
        pg.ENUM(
            DifficultyLevelType,
            name="difficulty_level_enum",
            create_type=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    """Required experience level to perform the exercise."""
    mechanic: Mapped[MechanicType] = mapped_column(
        pg.ENUM(
            MechanicType,
            name="mechanic_enum",
            create_type=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=True,
    )
    """Movement mechanic (compound or isolation)."""
    category: Mapped[CategoryType] = mapped_column(
        pg.ENUM(
            CategoryType,
            name="category_enum",
            create_type=False,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )
    """The primary fitness discipline or training goal."""
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Step-by-step guide on how to perform the movement."""
    image_path_start: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    """Relative path to the starting position image. Only for system-provided exercises."""
    image_path_end: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    """Relative path to the ending position image. Only for system-provided exercises."""
    is_system_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """Indicates if this is a system-provided exercise."""
    created_by: Mapped[GUID] = mapped_column(
        GUID,
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    """Reference to the user who created a custom exercise."""
    slug: Mapped[str] = mapped_column(String(100), nullable=True)
    """Unique URL-friendly identifier for system-default exercises."""

    __table_args__ = (
        Index(
            "uq_exercise_created_by_user",
            "created_by",
            "name",
            unique=True,
            postgresql_where=created_by.is_not(None),
        ),
        Index(
            "uq_sys_exercise_slug",
            "slug",
            unique=True,
            postgresql_where=is_system_default.is_(True),
        ),
        Index(
            "uq_sys_exercise_name",
            "name",
            unique=True,
            postgresql_where=is_system_default.is_(True),
        ),
        {"comment": "Core exercise definitions including mechanics, difficulty, and muscle targeting"},
    )

    # ------------
    # ORM Relationships
    # ------------
    primary_muscles: Mapped[list[MuscleGroup]] = relationship(
        secondary=exercise_primary_muscles,
        back_populates="primary_exercises",
        lazy="selectin",
    )
    """List of main target muscle groups."""
    secondary_muscles: Mapped[list[MuscleGroup]] = relationship(
        secondary=exercise_secondary_muscles,
        back_populates="secondary_exercises",
        lazy="selectin",
    )
    """List of assisting muscle groups."""
    equipment: Mapped[list[Equipment]] = relationship(
        secondary=exercise_equipment,
        back_populates="exercises_using",
        lazy="selectin",
    )
    """List of equipment required for the exercise."""
    tags: Mapped[list[ExerciseTag]] = relationship(
        secondary=exercise_tag_map,
        back_populates="tagged_exercises",
        lazy="selectin",
    )
    """System-defined metadata tags for categorization and filtering."""
