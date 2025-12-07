from typing import Annotated

from advanced_alchemy.extensions.fastapi import (
    AdvancedAlchemy,
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .base import get_settings

settings = get_settings()

sqlalchemy_config = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    commit_mode="autocommit",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)

alchemy: AdvancedAlchemy = AdvancedAlchemy(config=sqlalchemy_config)
DatabaseSession = Annotated[AsyncSession, Depends(alchemy.provide_session())]
