# Convention: fx_* — named fixtures, always requested via name=.
#              _* — infrastructure, never requested directly
#                       (autouse or helper-only).
#              Types and classes: plain names in test files.

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Set test environment BEFORE any app imports (settings are cached on first import)
load_dotenv(Path(__file__).resolve().parent.parent / ".env.testing", override=True)

# Now import app modules after environment is configured
from typing import TYPE_CHECKING, Any, NoReturn

import pytest
import structlog

if TYPE_CHECKING:
    from fastapi import FastAPI


pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker.postgres",
    "pytest_databases.docker.valkey",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(name="app")
def fx_app(
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    from app.server.core import create_app

    monkeypatch.setattr("app.server.core.configure_logging", lambda: None)
    return create_app()


@pytest.fixture(scope="session", autouse=True)
def _configure_structlog_for_tests() -> None:
    """Disable all logging output during test session by dropping all events."""

    def drop_everything(_logger: Any, _name: Any, _event_dict: Any) -> NoReturn:
        raise structlog.DropEvent

    structlog.configure(
        processors=[
            drop_everything,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
