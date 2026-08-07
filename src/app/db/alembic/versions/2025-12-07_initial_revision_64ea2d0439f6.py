"""Initial revision

Revision ID: 64ea2d0439f6
Revises: 
Create Date: 2025-12-07 14:44:59.625297+00:00

"""

import warnings
from typing import TYPE_CHECKING
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC, StoredObject, PasswordHash
from sqlalchemy import Text  # noqa: F401

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
sa.StoredObject = StoredObject

# revision identifiers, used by Alembic.
revision = '64ea2d0439f6'
down_revision = None
branch_labels = None
depends_on = None

alembic_dir = Path(__file__).resolve().parents[1]
sql_dir = alembic_dir / "sql"


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()

def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()

def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    sql_types_script = (sql_dir / "db_types.sql").read_text(encoding="utf-8")
    op.execute(sql_types_script)

def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.execute("""
        DROP TYPE IF EXISTS 
            sharing_status_enum,
            exercise_mode_enum,
            category_enum,
            mechanic_enum,
            difficulty_level_enum,
            force_enum;
    """)

def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""

def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
