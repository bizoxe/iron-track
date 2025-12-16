from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import SlugKey
from sqlalchemy import String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

if TYPE_CHECKING:
    from .user import User


class Role(UUIDv7AuditBase, SlugKey):
    """ORM Model representing user roles and permissions."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    """The unique, displayable name of the role (e.g., 'Superuser', 'Application Access')."""
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """A brief description of the role's purpose and permissions."""

    # -----------
    # ORM Relationships
    # ------------
    users: Mapped[list[User]] = relationship(
        back_populates="role",
        lazy="noload",
        viewonly=True,
    )
    """The list of users assigned to this role."""
