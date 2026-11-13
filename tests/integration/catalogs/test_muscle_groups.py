"""Mirror wiring tests for test_equipment.py.

Covers routes, schema signatures, access control, and this table's unique
index (duplicate names, retaken restores).

Shared catalog depth is pinned once in test_equipment.py; schema boundaries
live in the unit tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from fastapi import status
from sqlalchemy import func, select, text

from app.db.models.catalog import MuscleGroup

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio

# --- Fixtures ---

RETIRED_MUSCLE_GROUP_ID = 18
RETIRED_MUSCLE_GROUP_NAME = "obliques"


@pytest.fixture(name="retired_muscle_group")
async def fx_seed_retired_muscle_group(session: AsyncSession) -> None:
    session.add(
        MuscleGroup(id=RETIRED_MUSCLE_GROUP_ID, name=RETIRED_MUSCLE_GROUP_NAME, deleted_at=datetime.now(tz=UTC)),
    )
    await session.flush()
    await session.execute(
        text(
            f"SELECT setval(pg_get_serial_sequence('{MuscleGroup.__tablename__}', 'id'), "
            f"greatest(nextval(pg_get_serial_sequence('{MuscleGroup.__tablename__}', 'id')), {RETIRED_MUSCLE_GROUP_ID}))",
        ),
    )


# --- Create ---


@pytest.mark.parametrize(
    ("payload", "result", "status_code"),
    [
        pytest.param(
            {"name": "  Rear  DelTs  "},
            "rear delts",
            status.HTTP_201_CREATED,
            id="name_normalized_on_save",
        ),
        pytest.param({"name": "hamstrings"}, None, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_create_muscle_group(
    app: FastAPI,
    superuser_client: AsyncClient,
    payload: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("muscle_groups:create"),
        json=payload,
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


# --- List Muscle Groups ---


async def test_get_list_muscle_groups_returns_active_only(
    app: FastAPI,
    user_client: AsyncClient,
    session: AsyncSession,
) -> None:
    all_active_count = await session.scalar(select(func.count()).where(MuscleGroup.deleted_at.is_(None)))
    response = await user_client.get(app.url_path_for("muscle_groups:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == all_active_count
    assert all("deletedAt" not in item for item in response_data)


async def test_get_list_muscle_groups_search(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    response = await user_client.get(
        app.url_path_for("muscle_groups:list"),
        params={"searchString": "chest"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == "chest"


async def test_get_list_with_retired_muscle_groups(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_muscle_group: None,
) -> None:
    response = await superuser_client.get(
        app.url_path_for("muscle_groups:list-with-retired"),
        params={"showOnlyRetired": True},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert all(item["deletedAt"] is not None for item in response_data)
    assert RETIRED_MUSCLE_GROUP_NAME in {item["name"] for item in response_data}


# --- Get by ID ---


@pytest.mark.parametrize(
    ("muscle_id", "status_code"),
    [
        pytest.param(1, status.HTTP_200_OK, id="active_item"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(RETIRED_MUSCLE_GROUP_ID, status.HTTP_404_NOT_FOUND, id="retired_item_not_found"),
    ],
)
async def test_get_muscle_group(
    app: FastAPI,
    user_client: AsyncClient,
    retired_muscle_group: None,
    muscle_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("muscle_groups:get", muscle_id=muscle_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == muscle_id
        assert "deletedAt" not in response_data


# --- Update ---


async def test_update_muscle_group(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("muscle_groups:update", muscle_id=2),
        json={"name": "  HAMSTRINGS Updated  "},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == 2  # noqa: PLR2004
    assert response_data["name"] == "hamstrings updated"


@pytest.mark.parametrize(
    ("muscle_id", "payload", "status_code"),
    [
        pytest.param(2, {"name": "quadriceps"}, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param(999, {"name": "not found"}, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(4, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_update_muscle_group_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    muscle_id: int,
    payload: dict[str, str | None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("muscle_groups:update", muscle_id=muscle_id),
        json=payload,
    )
    assert response.status_code == status_code


# --- Restore ---


@pytest.mark.parametrize(
    ("payload", "expected_name"),
    [
        pytest.param({}, RETIRED_MUSCLE_GROUP_NAME, id="restored"),
        pytest.param(
            {"name": f"  {RETIRED_MUSCLE_GROUP_NAME.upper()} "},
            RETIRED_MUSCLE_GROUP_NAME,
            id="normalized_name_on_restore",
        ),
        pytest.param({"name": "serratus anterior"}, "serratus anterior", id="renamed_on_restore"),
    ],
)
async def test_restore_muscle_group(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_muscle_group: None,
    payload: dict[str, str],
    expected_name: str,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("muscle_groups:restore", muscle_id=RETIRED_MUSCLE_GROUP_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == RETIRED_MUSCLE_GROUP_ID
    assert response_data["name"] == expected_name
    assert "deletedAt" not in response_data


@pytest.mark.parametrize(
    ("muscle_id", "payload", "status_code"),
    [
        pytest.param(999, {}, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(1, {}, status.HTTP_409_CONFLICT, id="rejects_active_item"),
        pytest.param(
            4,
            {"name": None},
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="name_rejects_null",
        ),
    ],
)
async def test_restore_muscle_group_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    muscle_id: int,
    payload: dict[str, None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("muscle_groups:restore", muscle_id=muscle_id),
        json=payload,
    )
    assert response.status_code == status_code


async def test_restore_muscle_group_conflicts_when_name_retaken(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_muscle_group: None,
) -> None:
    created = await superuser_client.post(
        app.url_path_for("muscle_groups:create"),
        json={"name": RETIRED_MUSCLE_GROUP_NAME},
    )
    assert created.status_code == status.HTTP_201_CREATED

    restore = await superuser_client.patch(
        app.url_path_for("muscle_groups:restore", muscle_id=RETIRED_MUSCLE_GROUP_ID),
        json={},
    )
    assert restore.status_code == status.HTTP_409_CONFLICT


# --- Retire ---


@pytest.mark.parametrize(
    ("muscle_id", "status_code"),
    [
        pytest.param(3, status.HTTP_204_NO_CONTENT, id="retired"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
    ],
)
async def test_delete_muscle_group(
    app: FastAPI,
    superuser_client: AsyncClient,
    session: AsyncSession,
    muscle_id: int,
    status_code: int,
) -> None:
    response = await superuser_client.delete(app.url_path_for("muscle_groups:delete", muscle_id=muscle_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_204_NO_CONTENT:
        stmt = select(MuscleGroup).where(MuscleGroup.id == muscle_id).execution_options(include_deleted=True)
        retired_obj = await session.scalar(stmt)
        assert retired_obj is not None
        assert retired_obj.deleted_at is not None


# --- Access Control ---


@pytest.mark.parametrize(
    ("url_path", "method", "muscle_id"),
    [
        ("muscle_groups:create", "post", None),
        ("muscle_groups:list-with-retired", "get", None),
        ("muscle_groups:update", "patch", 1),
        ("muscle_groups:restore", "patch", 1),
        ("muscle_groups:delete", "delete", 1),
    ],
)
async def test_regular_user_forbidden_on_muscle_groups(
    app: FastAPI,
    user_client: AsyncClient,
    url_path: str,
    method: str,
    muscle_id: int | None,
) -> None:
    path_params = {"muscle_id": muscle_id} if muscle_id is not None else {}
    response = await getattr(user_client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("url_path", "method", "muscle_id"),
    [
        ("muscle_groups:create", "post", None),
        ("muscle_groups:list", "get", None),
        ("muscle_groups:list-with-retired", "get", None),
        ("muscle_groups:get", "get", 1),
        ("muscle_groups:update", "patch", 1),
        ("muscle_groups:restore", "patch", 1),
        ("muscle_groups:delete", "delete", 1),
    ],
)
async def test_muscle_group_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    url_path: str,
    method: str,
    muscle_id: int | None,
) -> None:
    path_params = {"muscle_id": muscle_id} if muscle_id is not None else {}
    response = await getattr(client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
