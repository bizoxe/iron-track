from advanced_alchemy.base import DefaultBase
from sqlalchemy import SmallInteger
from sqlalchemy.orm import Mapped, mapped_column


class SmallIntPKBase(DefaultBase):
    """Base model with a Small Integer primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
