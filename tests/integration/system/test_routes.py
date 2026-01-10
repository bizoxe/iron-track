from typing import TYPE_CHECKING

import pytest
from fastapi import status

from app.__about__ import __version__ as current_version
from app.config.base import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_system_health(
    app: "FastAPI",
    client: "AsyncClient",
) -> None:
    app_name = get_settings().app.NAME
    expected = {
        "database_status": "online",
        "cache_status": "online",
        "app": app_name,
        "version": current_version,
    }
    response = await client.get(app.url_path_for("system:health"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data == expected


async def test_ping(
    app: "FastAPI",
    client: "AsyncClient",
) -> None:
    response = await client.get(app.url_path_for("system:ping"))
    assert response.status_code == status.HTTP_200_OK
