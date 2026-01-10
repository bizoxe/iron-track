from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    NoReturn,
)
from unittest import mock

import pytest
import structlog
from redis.asyncio import Redis

from app.config import base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from pytest_databases.docker.redis import RedisService


pytestmark = pytest.mark.anyio

pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker.postgres",
    "pytest_databases.docker.redis",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def _path_settings() -> Generator[None, None, None]:
    """Patch the settings."""
    base_dir = Path(__file__).parent.parent
    env_testing_file = base_dir / ".env.testing"

    settings = base.Settings.from_env(dotenv_file=env_testing_file)
    with mock.patch.object(base, "get_settings", return_value=settings):
        yield


@pytest.fixture(scope="session", autouse=True)
def _configure_structlog_for_tests() -> None:
    """Disable all logging output during test session by dropping all events."""

    def drop_everything(_, __, ___) -> NoReturn:  # type: ignore[no-untyped-def] # noqa: ANN001
        raise structlog.DropEvent

    structlog.configure(
        processors=[
            drop_everything,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


@pytest.fixture(scope="session", name="redis")
async def fx_redis(redis_service: RedisService) -> AsyncGenerator[Redis, None]:
    """Redis instance for testing.

    Returns:
        Redis client instance, session scoped.
    """
    redis_client = Redis(host=redis_service.host, port=redis_service.port, db=redis_service.db)

    yield redis_client
    await redis_client.aclose()


@pytest.fixture(autouse=True)
async def _flush_redis_db(redis: Redis) -> None:
    await redis.flushdb()


@pytest.fixture(name="redis_client")
def fx_redis_client(redis: Redis) -> Redis:
    return redis
