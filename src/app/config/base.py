from __future__ import annotations

import json
import os
from contextlib import suppress
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Final

from joserfc.jwk import OKPKey
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.lib.exceptions import JWTKeyConfigError

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DEFAULT_DOTENV_FILE_PATH: Final[Path] = BASE_DIR / "config" / ".env"
TRUE_VALUES: Final[frozenset[str]] = frozenset({"True", "true", "1", "yes", "Y", "T"})


@dataclass
class AppSettings:
    """Application configuration."""

    DEBUG: bool = field(default_factory=lambda: os.getenv("FASTAPI_DEBUG", "False") in TRUE_VALUES)
    """FastAPI application debug mode."""
    NAME: str = field(default="IronTrack")
    """Application name."""
    ENVIRONMENT: str = field(default_factory=lambda: os.getenv("APP_ENVIRONMENT", "dev"))
    """Application execution environment (e.g., `dev`, `prod`)."""
    API_V1_URL_PREFIX: str = field(default="/api/v1")
    """Default URL prefix for API version routes."""
    COOKIE_SECURE_VALUE: bool = field(default_factory=lambda: os.getenv("COOKIE_SECURE", "False") in TRUE_VALUES)
    """Secure' flag for authentication cookies (requires HTTPS)."""
    CDN_BASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "CDN_BASE_URL", "https://raw.githubusercontent.com/bizoxe/iron-track/media/resources"
        ),
    )
    """Base CDN URL for hosted resources.

    Temporary: GitHub raw media branch; move to a dedicated CDN later.
    """
    CRYPTO_MAX_WORKERS: int | None = field(
        default_factory=lambda: int(val) if (val := os.getenv("CRYPTO_MAX_WORKERS")) is not None else None
    )
    """Maximum number of threads allocated for password hashing operations."""
    CATALOG_LIST_CACHE_TTL: str = field(
        default_factory=lambda: os.getenv("CATALOG_LIST_CACHE_TTL", "3h"),
    )
    """TTL for cached catalog lists."""

    _settings: Settings = field(init=False, repr=False)

    @property
    def user_auth_cache_ttl(self) -> str:
        """TTL for cached user authentication and authorization data."""
        return f"{self._settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES}m"

    @property
    def cdn_images_url_prefix(self) -> str:
        """Full CDN URL prefix for image resources."""
        base = self.CDN_BASE_URL.rstrip("/")
        return f"{base}/images"

    @property
    def crypto_workers(self) -> int:
        """Safe default thread count for password hashing."""
        if self.CRYPTO_MAX_WORKERS is not None:
            return self.CRYPTO_MAX_WORKERS

        cores = os.cpu_count() or 1
        if hasattr(os, "sched_getaffinity"):
            with suppress(Exception):
                cores = len(os.sched_getaffinity(0))

        return max(min(cores, 4), 1)


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
    """SQLAlchemy log level."""
    CASHEWS_LEVEL: int = field(default=40)
    """Fixed logging level for Cashews."""

    _settings: Settings = field(init=False, repr=False)

    @property
    def final_formatter(self) -> str:
        """Name of the logging formatter based on the current environment.

        `plain_console` for development, `json_console` otherwise.
        """
        if self._settings.app.ENVIRONMENT == "dev":
            return "plain_console"
        return "json_console"


@dataclass
class DatabaseSettings:
    """Database configuration."""

    POSTGRES_HOST: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    """PostgreSQL server hostname."""
    POSTGRES_PORT: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    """PostgreSQL server port number."""
    POSTGRES_USER: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    """PostgreSQL database username."""
    POSTGRES_PASSWORD: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "supersecretpassword"))
    """PostgreSQL database password."""
    POSTGRES_DB: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "iron_track"))
    """PostgreSQL database name."""
    DATABASE_URL: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    """Optional: Full, pre-configured database connection URL."""

    ECHO: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO", "False") in TRUE_VALUES)
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool = field(default_factory=lambda: os.getenv("DATABASE_ECHO_POOL", "False") in TRUE_VALUES)
    """Enable SQLAlchemy connection pool logs."""
    POOL_MAX_OVERFLOW: int = field(default_factory=lambda: int(os.getenv("DATABASE_MAX_POOL_OVERFLOW", "10")))
    """Maximum overflow for the SQLAlchemy connection pool."""
    POOL_SIZE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "5")))
    """Pool size for SQLAlchemy connection pool."""
    POOL_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    """Connection timeout, in seconds."""
    POOL_RECYCLE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_RECYCLE", "300")))
    """Amount of time to wait before recycling connections."""
    POOL_PRE_PING: bool = field(default_factory=lambda: os.getenv("DATABASE_PRE_POOL_PING", "False") in TRUE_VALUES)
    """Ping the database before fetching a connection from the pool."""
    POOL_DISABLED: bool = field(default_factory=lambda: os.getenv("DATABASE_POOL_DISABLED", "False") in TRUE_VALUES)
    """Disable SQLAlchemy pool configuration."""

    MIGRATION_CONFIG: str = field(default_factory=lambda: f"{BASE_DIR}/db/alembic/alembic.ini")
    """Path to the `alembic.ini` configuration file."""
    MIGRATION_PATH: str = field(default_factory=lambda: f"{BASE_DIR}/db/alembic")
    """Path to the `alembic` database migrations."""
    MIGRATION_DDL_VERSION_TABLE: str = field(default="ddl_version")
    """Name for the `alembic` versions table."""
    FIXTURE_PATH: str = field(default_factory=lambda: f"{BASE_DIR}/db/fixtures")
    """Path to JSON fixture files to load into tables."""
    PGBOUNCER_ENABLED: bool = field(default_factory=lambda: os.getenv("PGBOUNCER_ENABLED", "True") in TRUE_VALUES)
    """Enable PgBouncer connection pooling for SQLAlchemy."""

    _engine_instance: AsyncEngine | None = field(default=None, init=False, repr=False)

    def get_connection_url(self) -> URL:
        """Construct the full PostgreSQL connection URL.

        Prioritizes the explicit URL attribute if set.
        """
        if self.DATABASE_URL is not None:
            return make_url(self.DATABASE_URL)

        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def engine(self) -> AsyncEngine:
        """SQLAlchemy async engine instance for database operations."""
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
            echo_pool="debug" if self.ECHO_POOL else False,
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
        """Create the SQLAlchemy engine for PgBouncer compatibility.

        asyncpg's statement cache stays enabled: PgBouncer tracks prepared
        statements (`max_prepared_statements` in pgbouncer.ini), which makes
        it safe in transaction pooling mode.
        """
        if self._engine_instance is not None:
            return self._engine_instance

        engine = create_async_engine(
            url=self.get_connection_url(),
            echo=self.ECHO,
            poolclass=NullPool,
            execution_options={
                "isolation_level": "READ COMMITTED",
            },
            connect_args={
                "statement_cache_size": 100,
            },
        )
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class JWTSettings:
    """JWT configuration."""

    ALGORITHM: str = field(default="Ed25519")
    """Cryptographic algorithm used for JWS (JSON Web Signature)."""
    JWT_PRIVATE_KEY: str | None = field(default_factory=lambda: os.getenv("JWT_PRIVATE_KEY"))
    """Ed25519 private key in JWK (JSON Web Key) format.

    Used for both signing and verifying tokens with the fully-specified Ed25519 algorithm identifier
    (RFC 9864). The string must be a valid JSON containing 'kty', 'crv', 'x', and 'd' parameters.

    Example:
        '{"kty":"OKP","crv":"Ed25519","x":"...","d":"..."}'
    """
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )
    """Lifetime of the access token in minutes."""
    REFRESH_TOKEN_EXPIRE_DAYS: int = field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    """Lifetime of the refresh token in days."""

    @property
    def access_token_max_age(self) -> int:
        """Access token lifetime in cookies (calculated in seconds)."""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_max_age(self) -> int:
        """Refresh token lifetime in cookies (calculated in seconds)."""
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @cached_property
    def key_object(self) -> OKPKey:
        """Initialized Ed25519 key object for signing and verification.

        Raises:
            JWTKeyConfigError: If the key is missing, not valid JSON,
                or lacks required JWK parameters (kty, crv, x, d).
        """
        if self.JWT_PRIVATE_KEY is None:
            msg = "JWT_PRIVATE_KEY is not set. Security cannot start without a secret key."
            raise JWTKeyConfigError(message=msg)

        try:
            key_data = json.loads(self.JWT_PRIVATE_KEY)
            return OKPKey.import_key(key_data)
        except (TypeError, ValueError) as exc:
            msg = f"Failed to initialize Ed25519 key from JWT_PRIVATE_KEY: {exc}"
            raise JWTKeyConfigError(message=msg) from exc


@dataclass
class CacheSettings:
    """Cache configuration."""

    URL: str = field(default_factory=lambda: os.getenv("VALKEY_URL", "redis://localhost:6379/0"))
    """Valkey server connection URL."""

    _settings: Settings = field(init=False, repr=False)

    @property
    def suppress(self) -> bool:
        """Whether cache backend errors are suppressed outside development."""
        return self._settings.app.ENVIRONMENT != "dev"


@dataclass
class Settings:
    """Container class holding all application configuration settings.

    Attributes:
        app (AppSettings): Application-level settings.
        log (LogSettings): Logging configuration.
        db (DatabaseSettings): Database connection and pool settings.
        jwt (JWTSettings): JWT token configuration.
        cache (CacheSettings): Cache configuration.
    """

    app: AppSettings = field(default_factory=AppSettings)
    log: LogSettings = field(default_factory=LogSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    jwt: JWTSettings = field(default_factory=JWTSettings)
    cache: CacheSettings = field(default_factory=CacheSettings)

    def __post_init__(self) -> None:
        self.log._settings = self
        self.app._settings = self
        self.cache._settings = self

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
