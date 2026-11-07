from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.ext.associationproxy import (
    AssociationProxy,
    association_proxy,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    from .role import Role


class User(SoftDeleteMixin, UUIDv7AuditBase):
    """User account for application access."""

    __tablename__ = "user_account"
    __pii_columns__ = {"name", "email"}  # noqa: RUF012

    name: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    """User's full name."""
    email: Mapped[str] = mapped_column(String(length=255), nullable=False)
    """Unique email address for the user, used for login."""
    password: Mapped[str] = mapped_column(String(length=255), nullable=False, deferred=True)
    """Hashed password for authentication."""
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    """Indicates whether the user account is administratively banned."""
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    """Indicates if the user has administrative privileges."""
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, deferred=True)
    """Last successful login; None means user never logged in."""

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("role.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    """Foreign key linking to the user's role."""

    __table_args__ = (
        Index("uidx_user_account_email_lower", func.lower(email), unique=True),
        {"comment": "User accounts for application access"},
    )

    # ------------
    # ORM Relationships
    # ------------
    role: Mapped[Role] = relationship(lazy="selectin")
    """Role assigned to the user."""

    # ------------
    # Association Proxies
    # ------------
    role_name: AssociationProxy[str] = association_proxy("role", "name")
    """Proxy access to the name of the user's role."""
    role_slug: AssociationProxy[str] = association_proxy("role", "slug")
    """Proxy access to the slug (short identifier) of the user's role."""
