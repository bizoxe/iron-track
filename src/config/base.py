from __future__ import annotations

import os
from dataclasses import (
    dataclass,
    field,
)
from functools import lru_cache
from pathlib import Path
from typing import Final
from uuid import uuid4

from redis.asyncio import Redis
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
    POSTGRES_PASSWORD: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "supersecretpassword"))
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
    PGBOUNCER_ENABLED: bool = field(default_factory=lambda: os.getenv("BG_BOUNCER_ENABLED", "True") in TRUE_VALUES)

    _engine_instance: AsyncEngine | None = None

    def get_connection_url(self) -> str:
        if self.URL is not None:
            return self.URL

        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self.PGBOUNCER_ENABLED:
            return self.configure_pgbouncer_engine()
        return self.configure_standard_engine()

    def configure_standard_engine(self) -> AsyncEngine:
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

    def configure_pgbouncer_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance

        engine = create_async_engine(
            url=self.get_connection_url(),
            echo=self.ECHO,
            poolclass=NullPool,
            execution_options={
                "compiled_cache": None,
                "isolation_level": "READ COMMITTED",
            },
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
            },
        )
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class JWTSettings:
    """JWT configuration."""

    ALGORITHM: str = field(default_factory=lambda: os.getenv("ALGORITHM", "RS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")))
    TOKEN_URL: str = field(default_factory=lambda: os.getenv("TOKEN_URL", "/api/access/signin"))
    OAUTH_JWT_PRIVATE_KEY: Path = field(default_factory=lambda: BASE_DIR / "certs" / "private.pem")
    OAUTH_JWT_PUBLIC_KEY: Path = field(default_factory=lambda: BASE_DIR / "certs" / "public.pem")


@dataclass
class RedisSettings:
    """Redis configuration."""

    URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    """Redis connection URL."""
    SOCKET_CONNECT_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")))
    """Length of time to wait (in seconds) for a connection to become active."""
    HEALTH_CHECK_INTERVAL: int = field(default_factory=lambda: int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "5")))
    """Length of time to wait (in seconds) before testing connection health."""
    SOCKET_KEEPALIVE: bool = field(default_factory=lambda: os.getenv("REDIS_SOCKET_KEEPALIVE", "True") in TRUE_VALUES)
    """Length of time to wait (in seconds) between keepalive commands."""

    @property
    def client(self) -> Redis:
        return self.get_client()

    def get_client(self) -> Redis:
        redis_client: Redis = Redis.from_url(
            url=self.URL,
            encoding="utf-8",
            decode_responses=False,  # must be set to False, important for fastapi-cache
            socket_connect_timeout=self.SOCKET_CONNECT_TIMEOUT,
            socket_keepalive=self.SOCKET_KEEPALIVE,
            health_check_interval=self.HEALTH_CHECK_INTERVAL,
        )
        return redis_client


@dataclass
class Settings:
    log: LogSettings = field(default_factory=LogSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    jwt: JWTSettings = field(default_factory=JWTSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        env_file = BASE_DIR / "config" / dotenv_filename
        if env_file.is_file():
            from dotenv import load_dotenv

            load_dotenv(env_file, override=True)

        return Settings()


def get_settings() -> Settings:
    return Settings.from_env()
