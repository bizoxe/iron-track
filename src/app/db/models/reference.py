from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import orm_registry
from advanced_alchemy.types import GUID
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Table,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.models.base import SmallIntPKBase

if TYPE_CHECKING:
    from .exercise import Exercise

# --- Association Tables ---


exercise_primary_muscles = Table(
    "exercise_primary_muscles",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "muscle_group_id",
        ForeignKey("muscle_groups.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_ex_primary_muscle_id", "muscle_group_id"),
    comment="M2M: Link between exercises and their prime mover muscle groups",
)
"""Association table linking exercises to their primary target muscle groups."""


exercise_secondary_muscles = Table(
    "exercise_secondary_muscles",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "muscle_group_id",
        ForeignKey("muscle_groups.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_ex_secondary_muscle_id", "muscle_group_id"),
    comment="M2M: Link between exercises and their synergist/stabilizer muscle groups",
)
"""Association table linking exercises to their secondary (synergist) muscle groups."""


exercise_equipment = Table(
    "exercise_equipment",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "equipment_id",
        ForeignKey("equipment.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_ex_equipment_id", "equipment_id"),
    comment="M2M: Link between exercises and required equipment",
)
"""Association table linking exercises to the required equipment."""


exercise_tag_map = Table(
    "exercise_tag_map",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercises.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "tag_id",
        ForeignKey("exercise_tags.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_ex_tag_map_tag_id", "tag_id"),
    comment="M2M: Link between exercises and functional/biomechanical tags",
)
"""Association table linking exercises to system-defined metadata tags."""

# --- Models ---


class MuscleGroup(SmallIntPKBase):
    """Anatomical muscle group used to categorize exercises and track targeting."""

    __tablename__ = "muscle_groups"

    __table_args__ = ({"comment": "Anatomical muscle groups for exercise targeting (e.g., biceps, triceps)"},)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    """Normalized lowercase name of the muscle group."""

    # ------------
    # ORM Relationships
    # ------------
    primary_exercises: Mapped[list[Exercise]] = relationship(
        secondary=exercise_primary_muscles,
        back_populates="primary_muscles",
        lazy="noload",
        viewonly=True,
    )
    """Exercises where this muscle is the prime mover (read-only)."""
    secondary_exercises: Mapped[list[Exercise]] = relationship(
        secondary=exercise_secondary_muscles,
        back_populates="secondary_muscles",
        lazy="noload",
        viewonly=True,
    )
    """Exercises where this muscle acts as a synergist or stabilizer (read-only)."""


class Equipment(SmallIntPKBase):
    """Physical tools or machines required to perform specific exercises."""

    __tablename__ = "equipment"

    __table_args__ = ({"comment": "Training equipment and machines (e.g., barbell, dumbbell, cable)"},)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    """Normalized lowercase name of the equipment."""

    # ------------
    # ORM Relationships
    # ------------
    exercises_using: Mapped[list[Exercise]] = relationship(
        secondary=exercise_equipment,
        back_populates="equipment",
        lazy="noload",
        viewonly=True,
    )
    """Collection of exercises that utilize this equipment (read-only)."""


class ExerciseTag(SmallIntPKBase):
    """Flexible metadata labels used for grouping and filtering exercises."""

    __tablename__ = "exercise_tags"

    __table_args__ = ({"comment": "Functional, environmental, and biomechanical exercise tags"},)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    """Normalized lowercase tag name."""
    # ------------
    # ORM Relationships
    # ------------
    tagged_exercises: Mapped[list[Exercise]] = relationship(
        secondary=exercise_tag_map,
        back_populates="tags",
        lazy="noload",
        viewonly=True,
    )
    """Collection of exercises associated with this metadata tag (read-only)."""
