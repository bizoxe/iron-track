from __future__ import annotations

import os
from dataclasses import (
    dataclass,
    field,
)
from functools import lru_cache
from pathlib import Path
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

BASE_DIR: Final[Path] = Path(__file__).parent.parent
TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class LogSettings:
    """Logger configuration."""

    LEVEL: int = field(default_factory=lambda: int(os.getenv("LOG_LEVEL", "20")))
    UVICORN_ACCESS_LEVEL: int = field(default_factory=lambda: int(os.getenv("UVICORN_ACCESS_LEVEL", "30")))
    UVICORN_ERROR_LEVEL: int = field(default_factory=lambda: int(os.getenv("UVICORN_ERROR_LEVEL", "20")))
    LOG_DIR: Path = field(default_factory=lambda: BASE_DIR.joinpath(os.getenv("LOG_DIR", "logs")))
    SQLALCHEMY_LEVEL: int = field(default_factory=lambda: int(os.getenv("SQLALCHEMY_LEVEL", "30")))
    """SQLAlchemy logs level."""


@dataclass
class DatabaseSettings:
    """Database configuration."""

    POSTGRES_HOST: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    POSTGRES_PORT: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    POSTGRES_USER: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    POSTGRES_PASSWORD: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "secretpwd"))
    POSTGRES_DB: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "iron_track"))
    URL: str | None = None

    ECHO: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO", "False") in TRUE_VALUES)
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO_POOL", "False") in TRUE_VALUES)
    """Enable SQLAlchemy connection pool logs."""
    POOL_MAX_OVERFLOW: int = field(default_factory=lambda: int(os.getenv("DATABASE_MAX_POOL_OVERFLOW", "10")))
    """Max overflow for SQLAlchemy connection pool"""
    POOL_SIZE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "5")))
    """Pool size for SQLAlchemy connection pool"""
    POOL_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    """Time in seconds for timing connections out of the connection pool."""
    POOL_RECYCLE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_RECYCLE", "300")))
    """Amount of time to wait before recycling connections."""
    POOL_PRE_PING: bool = field(default_factory=lambda: os.getenv("DATABASE_PRE_POOL_PING", "False") in TRUE_VALUES)
    """Optionally ping database before fetching a session from the connection pool."""
    POOL_DISABLED: bool = field(default_factory=lambda: os.getenv("DATABASE_POOL_DISABLED", "False") in TRUE_VALUES)
    """Disable SQLAlchemy pool configuration."""

    MIGRATION_CONFIG: str = field(
        default_factory=lambda: os.getenv("DATABASE_MIGRATION_CONFIG", f"{BASE_DIR}/db/alembic/alembic.ini")
    )
    MIGRATION_PATH: str = field(default_factory=lambda: os.getenv("DATABASE_MIGRATION_PATH", f"{BASE_DIR}/db/alembic"))
    MIGRATION_DDL_VERSION_TABLE: str = field(
        default_factory=lambda: os.getenv("DATABASE_MIGRATION_DDL_VERSION_TABLE", "ddl_version")
    )

    _engine_instance: AsyncEngine | None = None

    def get_connection_url(self) -> str:
        if self.URL is not None:
            return self.URL

        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance

        engine = create_async_engine(
            url=self.get_connection_url(),
            echo=self.ECHO,
            echo_pool=self.ECHO_POOL,
            max_overflow=self.POOL_MAX_OVERFLOW,
            pool_size=self.POOL_SIZE,
            pool_timeout=self.POOL_TIMEOUT,
            pool_recycle=self.POOL_RECYCLE,
            pool_pre_ping=self.POOL_PRE_PING,
            pool_use_lifo=True,  # use lifo to reduce the number of idle connections
            poolclass=NullPool if self.POOL_DISABLED else None,
        )
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class Settings:
    log: LogSettings = field(default_factory=LogSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        if env_file.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_file, override=True)

        return Settings()


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings.from_env()
