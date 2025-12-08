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
    __tablename__ = "user_account"
    __table_args__ = {"comment": "Users accounts for application access"}  # noqa: RUF012
    __pii_columns__ = {"name", "email"}  # noqa: RUF012

    name: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    email: Mapped[str] = mapped_column(String(length=255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(
        PasswordHash(backend=PwdlibHasher(hasher=PwdlibArgon2Hasher())),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    joined_at: Mapped[date] = mapped_column(Date, default=date.today)

    role_id: Mapped[UUID] = mapped_column(GUID, ForeignKey("role.id", ondelete="RESTRICT"), nullable=False)

    # ------------
    # ORM Relationships
    # ------------
    role: Mapped[Role] = relationship(back_populates="users", lazy="selectin")
    role_name: AssociationProxy[str] = association_proxy("role", "name")
    role_slug: AssociationProxy[str] = association_proxy("role", "slug")
