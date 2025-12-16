from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import (
    GUID,
    PasswordHash,
)
from advanced_alchemy.types.password_hash.pwdlib import PwdlibHasher
from pwdlib.hashers.argon2 import Argon2Hasher as PwdlibArgon2Hasher
from sqlalchemy import (
    Date,
    ForeignKey,
    String,
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

if TYPE_CHECKING:
    from .role import Role


class User(UUIDv7AuditBase):
    """ORM Model representing a user account in the application."""

    __tablename__ = "user_account"
    __table_args__ = {"comment": "Users accounts for application access"}  # noqa: RUF012
    __pii_columns__ = {"name", "email"}  # noqa: RUF012

    name: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    """The user's full name."""
    email: Mapped[str] = mapped_column(String(length=255), unique=True, nullable=False, index=True)
    """The unique email address for the user, used for login."""
    password: Mapped[str] = mapped_column(
        PasswordHash(backend=PwdlibHasher(hasher=PwdlibArgon2Hasher())),
        nullable=False,
    )
    """The Argon2 hashed password for authentication."""
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    """Indicates if the user account is active."""
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    """Indicates if the user has administrative privileges."""
    joined_at: Mapped[date] = mapped_column(Date, default=date.today)
    """The date the user account was created."""

    role_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("role.id", ondelete="RESTRICT"), nullable=False)
    """Foreign key linking to the user's role (Role.id)."""

    # ------------
    # ORM Relationships
    # ------------
    role: Mapped[Role] = relationship(back_populates="users", lazy="selectin")
    """The ORM relationship to the user's Role model."""
    role_name: AssociationProxy[str] = association_proxy("role", "name")
    """Proxy access to the name of the user's role."""
    role_slug: AssociationProxy[str] = association_proxy("role", "slug")
    """Proxy access to the slug (short identifier) of the user's role."""
