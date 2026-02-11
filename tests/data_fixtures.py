from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest

from app.config.constants import DEFAULT_ADMIN_EMAIL

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.anyio


@pytest.fixture(name="app")
def fx_app(
    pytestconfig: pytest.Config,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    """Create and configure the FastAPI application for testing.

    Returns:
        FastAPI: The configured application instance.
    """
    from app.server.core import create_app

    return create_app()


@pytest.fixture(scope="session", name="raw_users")
def fx_raw_users() -> list[dict[str, Any]]:
    """Unstructured user representations."""
    return [
        {
            "id": "019a536a-5d4e-7703-896d-1eaa79d993cf",
            "email": DEFAULT_ADMIN_EMAIL,
            "name": "System Administrator",
            "password": "Test_Password0!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": "019a53be-bec9-7120-81a2-8a46e85f22a4",
            "email": "superuser@example.com",
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
        },
        {
            "id": "019a5f0c-3a24-7693-abf4-3ed68ea9cf01",
            "email": "user@example.com",
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "019a643b-fe1e-7ae2-9fda-c45f3b77c3cb",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
        },
        {
            "id": "019a643f-5947-7110-8b7d-5b5be844de8e",
            "email": "fitness.trainer@example.com",
            "name": "Fitness Trainer",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "019a643e-db0a-77d0-89a6-0536f6d00a24",
            "email": "another@example.com",
            "name": "Another User",
            "password": "Test_Password4!",
            "is_superuser": False,
            "is_active": True,
        },
    ]
