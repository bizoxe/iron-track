from __future__ import annotations

import json
import os
from dataclasses import (
    dataclass,
    field,
)
from functools import (
    cached_property,
    lru_cache,
)
from pathlib import Path
from typing import Final

from joserfc.jwk import OKPKey
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.lib.exceptions import JWTKeyConfigError

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DEFAULT_DOTENV_FILE_PATH: Final[Path] = BASE_DIR / "config" / ".env"
TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class AppSettings:
    """Application configuration."""

    DEBUG: bool = field(default_factory=lambda: os.getenv("FASTAPI_DEBUG", "False") in TRUE_VALUES)
    """Whether to run the FastAPI application in debug mode."""
    NAME: str = field(default="IronTrack")
    """Application name."""
    ENVIRONMENT: str = field(default_factory=lambda: os.getenv("APP_ENVIRONMENT", "dev"))
    """The application execution environment (e.g., 'dev', 'prod')."""
    API_V1_URL_PREFIX: str = field(default="/api/v1")
    """The default URL prefix for API Version routes."""
    CDN_IMAGES_DEFAULT_URL: str = field(
        default_factory=lambda: os.getenv(
            "CDN_IMAGES_URL", "https://raw.githubusercontent.com/bizoxe/iron-track/media/resources/exercises"
        ),
    )
    """The default base URL for CDN-hosted exercise images."""


@dataclass
class LogSettings:
    """Logger configuration."""

    LEVEL: int = field(default_factory=lambda: int(os.getenv("LOG_LEVEL", "30")))
    """Standard library log level for the root logger."""
    STRUCTLOG_LEVEL: int = field(default=20)
    """Fixed structlog filtering level.

    Must be **20 (INFO)** to ensure middleware logs are not dropped before reaching
    the standard logging library.
    """
    ASGI_ACCESS_LEVEL: int = field(default_factory=lambda: int(os.getenv("ASGI_ACCESS_LEVEL", "40")))
    """Logging level for the server's internal access logs."""
    ASGI_ERROR_LEVEL: int = field(default_factory=lambda: int(os.getenv("ASGI_ERROR_LEVEL", "20")))
    """Logging level for the server's runtime events and errors."""
    MIDDLEWARE_LOG_LEVEL: int = field(default=20)
    """Fixed logging level for the ASGI access middleware.

    Must be **20 (INFO)**. Higher levels disable tracking of important requests needed for traffic
    monitoring and analysis.
    """
    SQLALCHEMY_LEVEL: int = field(default_factory=lambda: int(os.getenv("SQLALCHEMY_LEVEL", "30")))
    """SQLAlchemy logs level."""

    _settings: Settings = field(init=False, repr=False)

    @property
    def final_formatter(self) -> str:
        """The name of the logging formatter based on the current environment.

        Returns:
            str: 'plain_console' for development, 'json_console' otherwise.
        """
        if self._settings.app.ENVIRONMENT == "dev":
            return "plain_console"
        return "json_console"


@dataclass
class DatabaseSettings:
    """Database configuration."""

    POSTGRES_HOST: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    """The PostgreSQL server hostname."""
    POSTGRES_PORT: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    """The PostgreSQL server port number."""
    POSTGRES_USER: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    """The PostgreSQL database username."""
    POSTGRES_PASSWORD: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "supersecretpassword"))
    """The PostgreSQL database password."""
    POSTGRES_DB: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "iron_track"))
    """The PostgreSQL database name."""
    URL: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    """Optional: The full, pre-configured database connection URL."""

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

    MIGRATION_CONFIG: str = field(default_factory=lambda: f"{BASE_DIR}/db/alembic/alembic.ini")
    """The path to the `alembic.ini` configuration file."""
    MIGRATION_PATH: str = field(default_factory=lambda: f"{BASE_DIR}/db/alembic")
    """The path to the `alembic` database migrations."""
    MIGRATION_DDL_VERSION_TABLE: str = field(default="ddl_version")
    """The name to use for the `alembic` versions table name."""
    FIXTURE_PATH: str = field(default_factory=lambda: f"{BASE_DIR}/db/fixtures")
    """The path to JSON fixture files to load into tables."""
    PGBOUNCER_ENABLED: bool = field(default_factory=lambda: os.getenv("PGBOUNCER_ENABLED", "True") in TRUE_VALUES)
    """Enable PgBouncer connection pooling for SQLAlchemy."""

    _engine_instance: AsyncEngine | None = field(default=None, init=False)

    def get_connection_url(self) -> str:
        """Construct the full PostgreSQL connection URL.

        The method prioritizes the explicit URL attribute if it is set.

        Returns:
            str: The full connection URL string.
        """
        if self.URL is not None:
            return self.URL

        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def engine(self) -> AsyncEngine:
        """The SQLAlchemy async engine instance for database operations."""
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        """Retrieve or initialize the appropriate SQLAlchemy engine."""
        if self.PGBOUNCER_ENABLED:
            return self.configure_pgbouncer_engine()
        return self.configure_standard_engine()

    def configure_standard_engine(self) -> AsyncEngine:
        """Create and configure the standard SQLAlchemy async engine with pooling."""
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
        """Create the SQLAlchemy engine for PgBouncer compatibility."""
        if self._engine_instance is not None:
            return self._engine_instance

        engine = create_async_engine(
            url=self.get_connection_url(),
            echo=self.ECHO,
            echo_pool=self.ECHO_POOL,
            poolclass=NullPool,
            execution_options={
                "compiled_cache": None,
                "isolation_level": "READ COMMITTED",
            },
            connect_args={
                "statement_cache_size": 0,
            },
        )
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class JWTSettings:
    """JWT configuration."""

    ALGORITHM: str = field(default="Ed25519")
    """The cryptographic algorithm used for JWS (JSON Web Signature)."""
    JWT_PRIVATE_KEY: str | None = field(default_factory=lambda: os.getenv("JWT_PRIVATE_KEY"))
    """The `Ed25519` private key in JWK (JSON Web Key) format.

    This key is used for both signing and verifying tokens using the Ed25519 algorithm as specified
    in RFC 9864. The string must be a valid JSON containing 'kty', 'crv', 'x', and 'd' parameters.

    Example:
        '{"kty":"OKP","crv":"Ed25519","x":"...","d":"..."}'
    """
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )
    """Lifetime of the access token in minutes."""
    REFRESH_TOKEN_EXPIRE_DAYS: int = field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")))
    """Lifetime of the refresh token in days."""

    @cached_property
    def key_object(self) -> OKPKey:
        """The initialized Ed25519 key object for signing and verification.

        Parses the JWT_PRIVATE_KEY from environment variables and returns
        a ready-to-use OKPKey instance.

        Returns:
            OKPKey: The cryptographic key object for Ed25519 operations.

        Raises:
            JWTKeyConfigError: If the key is missing, not a valid JSON,
                or lacks required JWK parameters (kty, crv, x, d).
        """
        if self.JWT_PRIVATE_KEY is None:
            msg = "JWT_PRIVATE_KEY is not set. Security cannot start without a secret key."
            raise JWTKeyConfigError(message=msg)

        try:
            key_data = json.loads(self.JWT_PRIVATE_KEY)
            return OKPKey.import_key(key_data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            msg = f"Failed to initialize Ed25519 key from JWT_PRIVATE_KEY: {exc}"
            raise JWTKeyConfigError(message=msg) from exc


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

    _client: Redis | None = field(default=None, init=False, repr=False)

    @property
    def client(self) -> Redis:
        """The configured asynchronous Redis client instance."""
        if self._client is None:
            self._client = self.get_client()
        return self._client

    def get_client(self) -> Redis:
        """Initialize and configure the asynchronous Redis client."""
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
    """Container class holding all application configuration settings.

    Attributes:
        app (AppSettings): Application-level settings.
        log (LogSettings): Logging configuration.
        db (DatabaseSettings): Database connection and pool settings.
        jwt (JWTSettings): JWT token configuration.
        redis (RedisSettings): Redis client and connection settings.
    """

    app: AppSettings = field(default_factory=AppSettings)
    log: LogSettings = field(default_factory=LogSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    jwt: JWTSettings = field(default_factory=JWTSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)

    def __post_init__(self) -> None:
        self.log._settings = self  # noqa: SLF001

    @classmethod
    def from_env(cls, dotenv_file: Path) -> Settings:
        """Load environment variables from a dotenv file and initialize settings."""
        if dotenv_file.is_file():
            from dotenv import load_dotenv

            load_dotenv(dotenv_file, override=True)

        return cls()


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    """Load and cache application configuration."""
    return Settings.from_env(dotenv_file=DEFAULT_DOTENV_FILE_PATH)
