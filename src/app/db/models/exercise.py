from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.enums import pg_enum
from app.db.models.catalog import exercise_equipment, exercise_tag
from app.domain.enums import (
    Category,
    DifficultyLevel,
    Force,
    Mechanic,
    MuscleRole,
)

if TYPE_CHECKING:
    from .catalog import Equipment, ExerciseMuscle, MuscleGroup, Tag


class Exercise(UUIDv7AuditBase):
    """Physical exercise and its biomechanical properties."""

    __tablename__ = "exercise"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """Display name of the exercise."""
    force: Mapped[Force | None] = mapped_column(
        pg_enum(Force),
        nullable=True,
    )
    """Type of force or action involved in the exercise."""
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        pg_enum(DifficultyLevel),
        nullable=False,
    )
    """Difficulty level of the exercise."""
    mechanic: Mapped[Mechanic | None] = mapped_column(
        pg_enum(Mechanic),
        nullable=True,
    )
    """Mechanical action of the exercise."""
    category: Mapped[Category] = mapped_column(
        pg_enum(Category),
        nullable=False,
    )
    """Primary fitness category or discipline of the exercise."""
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Step-by-step guide on how to perform the exercise."""
    image_start_path: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    """Relative path to the starting-position image for a system-provided exercise."""
    image_end_path: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    """Relative path to the ending-position image for a system-provided exercise."""
    is_system_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    """Indicates if this is a system-provided exercise."""
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    """Reference to the user who created a custom exercise."""
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    """URL-friendly identifier for the exercise."""

    __table_args__ = (
        CheckConstraint(
            "NOT is_system_default OR created_by IS NULL",
            name="chk_exercise_system_no_author",
        ),
        Index(
            "uidx_exercise_created_by_slug",
            "created_by",
            "slug",
            unique=True,
            postgresql_where=created_by.is_not(None),
        ),
        Index(
            "uidx_exercise_system",
            "slug",
            unique=True,
            postgresql_where=is_system_default.is_(True),
        ),
        {"comment": "Core exercise definitions and fitness properties"},
    )

    # ------------
    # ORM Relationships
    # ------------
    exercise_muscles: Mapped[list[ExerciseMuscle]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    """Muscle groups targeted by the exercise, with their assigned roles."""
    equipment: Mapped[list[Equipment]] = relationship(
        secondary=exercise_equipment,
        lazy="selectin",
    )
    """Equipment required for the exercise."""
    tags: Mapped[list[Tag]] = relationship(
        secondary=exercise_tag,
        lazy="selectin",
    )
    """System-defined metadata tags for categorization and filtering."""

    @property
    def primary_muscles(self) -> list[MuscleGroup]:
        return [em.muscle_group for em in self.exercise_muscles if em.muscle_role is MuscleRole.PRIMARY]

    @property
    def secondary_muscles(self) -> list[MuscleGroup]:
        return [em.muscle_group for em in self.exercise_muscles if em.muscle_role is MuscleRole.SECONDARY]
