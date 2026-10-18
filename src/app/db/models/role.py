from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import SlugKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Role(UUIDv7AuditBase, SlugKey):
    """User role and permissions definition."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    """Unique, displayable name of the role (e.g., 'Superuser', 'Application Access')."""
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Brief description of the role's purpose and permissions."""
