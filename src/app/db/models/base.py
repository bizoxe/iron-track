from advanced_alchemy.base import DefaultBase
from sqlalchemy import (
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


class IntegerPKBase(DefaultBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class SmallIntPKBase(DefaultBase):
    """Base model with a Small Integer primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    """The primary key of the table."""
