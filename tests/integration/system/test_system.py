from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest
from cashews.exceptions import CacheBackendInteractionError
from fastapi import status
from sqlalchemy.exc import OperationalError
from structlog.testing import capture_logs

from app.domain.system.schemas import SystemHealth

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from pytest_mock import MockerFixture
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


async def test_check_system_health(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    expected_obj = SystemHealth(
        database_status="online",
        cache_status="online",
    )
    expected = asdict(expected_obj)
    response = await client.get(app.url_path_for("system:health"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data == expected


async def test_check_system_health_db_offline(
    app: FastAPI,
    client: AsyncClient,
    session: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """A dead database degrades probe to 503/offline and logs a warning."""
    mocker.patch.object(
        session,
        "execute",
        new_callable=mocker.AsyncMock,
        side_effect=OperationalError("SELECT 1", None, RuntimeError("connection refused")),
    )
    with capture_logs() as logs:
        response = await client.get(app.url_path_for("system:health"))
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    response_data = response.json()
    assert response_data["database_status"] == "offline"
    assert response_data["cache_status"] == "online"
    warning = next(log for log in logs if log["log_level"] == "warning")
    assert warning["database_status"] == "offline"
    assert "connection refused" in warning["database_error"]


async def test_check_system_health_cache_offline(
    app: FastAPI,
    client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    """A dead cache degrades probe to 503/offline and logs a warning."""
    mocker.patch(
        "app.domain.system.controllers.cache.ping",
        new_callable=mocker.AsyncMock,
        side_effect=CacheBackendInteractionError("valkey refused"),
    )
    with capture_logs() as logs:
        response = await client.get(app.url_path_for("system:health"))
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    response_data = response.json()
    assert response_data["database_status"] == "online"
    assert response_data["cache_status"] == "offline"
    warning = next(log for log in logs if log["log_level"] == "warning")
    assert warning["cache_status"] == "offline"
    assert "valkey refused" in warning["cache_error"]


async def test_ping(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    response = await client.get(app.url_path_for("system:ping"))
    assert response.status_code == status.HTTP_200_OK
