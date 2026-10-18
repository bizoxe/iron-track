from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import DefaultBase, orm_registry
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
    declared_attr,
    mapped_column,
    relationship,
)

from app.db.enums import pg_enum
from app.db.models.base import SmallIntPKBase
from app.db.models.mixins import SoftDeleteMixin
from app.domain.enums import MuscleRole

if TYPE_CHECKING:
    from .exercise import Exercise

# --- Association Objects ---


class ExerciseMuscle(DefaultBase):
    """Exercise muscle targeting.

    One muscle group in one role for one exercise (PK excludes the role:
    the same muscle cannot be both primary and secondary).
    """

    __tablename__ = "exercise_muscle"

    exercise_id: Mapped[UUID] = mapped_column(ForeignKey("exercise.id", ondelete="CASCADE"), primary_key=True)
    muscle_group_id: Mapped[int] = mapped_column(ForeignKey("muscle_group.id", ondelete="CASCADE"), primary_key=True)
    muscle_role: Mapped[MuscleRole] = mapped_column(pg_enum(MuscleRole), nullable=False)

    __table_args__ = (
        Index(
            "idx_exercise_muscle_muscle_group_id_muscle_role",
            "muscle_group_id",
            "muscle_role",
        ),
        {"comment": "Muscle groups targeted by exercise with assigned roles"},
    )

    # ------------
    # ORM Relationships
    # ------------
    exercise: Mapped[Exercise] = relationship(back_populates="exercise_muscles")
    muscle_group: Mapped[MuscleGroup] = relationship(lazy="joined", innerjoin=True)


# --- Association Tables ---


exercise_equipment = Table(
    "exercise_equipment",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercise.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "equipment_id",
        ForeignKey("equipment.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_exercise_equipment_equipment_id", "equipment_id"),
    comment="M2M: Link between exercise and required equipment",
)
"""Association table linking exercise to the required equipment."""


exercise_tag = Table(
    "exercise_tag",
    orm_registry.metadata,
    Column(
        "exercise_id",
        ForeignKey("exercise.id", ondelete="CASCADE"),
        primary_key=True,
        type_=GUID,
    ),
    Column(
        "tag_id",
        ForeignKey("tag.id", ondelete="CASCADE"),
        primary_key=True,
        type_=SmallInteger,
    ),
    Index("idx_exercise_tag_tag_id", "tag_id"),
    comment="M2M: Link between exercise and functional/biomechanical tags",
)
"""Association table linking exercise to system-defined metadata tags."""

# --- Models ---


class CatalogBase(SoftDeleteMixin, SmallIntPKBase):
    """Abstract base for bounded catalog entities."""

    __abstract__ = True

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """Normalized lowercase name."""


class MuscleGroup(CatalogBase):
    """Anatomical muscle group used to categorize exercise and track targeting."""

    __tablename__ = "muscle_group"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, dict[str, Any]]:  # noqa: N805
        return (
            Index(
                "uidx_muscle_group_name",
                cls.name,
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),  # type: ignore[union-attr]
            ),
            {"comment": "Anatomical muscle groups for exercise targeting (e.g., biceps, triceps)"},
        )


class Equipment(CatalogBase):
    """Tools or machines required to perform a specific exercise."""

    __tablename__ = "equipment"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, dict[str, Any]]:  # noqa: N805
        return (
            Index(
                "uidx_equipment_name",
                cls.name,
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),  # type: ignore[union-attr]
            ),
            {"comment": "Training equipment and machines (e.g., barbell, dumbbell, cable)"},
        )


class Tag(CatalogBase):
    """Flexible metadata labels for grouping and filtering exercise."""

    __tablename__ = "tag"

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, dict[str, Any]]:  # noqa: N805
        return (
            Index(
                "uidx_tag_name",
                cls.name,
                unique=True,
                postgresql_where=cls.deleted_at.is_(None),  # type: ignore[union-attr]
            ),
            {"comment": "Functional, environmental, and biomechanical exercise tags"},
        )
