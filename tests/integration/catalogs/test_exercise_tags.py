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

from app.db.models.catalog import Tag

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.anyio

# --- Fixtures ---

RETIRED_EXERCISE_TAG_ID = 26
RETIRED_EXERCISE_TAG_NAME = "low impact"


@pytest.fixture(name="retired_exercise_tag")
async def fx_seed_retired_exercise_tag(session: AsyncSession) -> None:
    session.add(
        Tag(id=RETIRED_EXERCISE_TAG_ID, name=RETIRED_EXERCISE_TAG_NAME, deleted_at=datetime.now(tz=UTC)),
    )
    await session.flush()
    await session.execute(
        text(
            f"SELECT setval(pg_get_serial_sequence('{Tag.__tablename__}', 'id'), "
            f"greatest(nextval(pg_get_serial_sequence('{Tag.__tablename__}', 'id')), {RETIRED_EXERCISE_TAG_ID}))",
        ),
    )


# --- Create ---


@pytest.mark.parametrize(
    ("payload", "result", "status_code"),
    [
        pytest.param(
            {"name": "  Pro-AthleTe  "},
            "pro-athlete",
            status.HTTP_201_CREATED,
            id="name_normalized_on_save",
        ),
        pytest.param({"name": "home friendly"}, None, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_create_exercise_tag(
    app: FastAPI,
    superuser_client: AsyncClient,
    payload: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("exercise_tags:create"),
        json=payload,
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


# --- List Exercise Tags ---


async def test_get_list_exercise_tags_returns_active_only(
    app: FastAPI,
    user_client: AsyncClient,
    session: AsyncSession,
) -> None:
    all_active_count = await session.scalar(select(func.count()).where(Tag.deleted_at.is_(None)))
    response = await user_client.get(app.url_path_for("exercise_tags:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == all_active_count
    assert all("deletedAt" not in item for item in response_data)


async def test_get_list_exercise_tags_search(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    response = await user_client.get(
        app.url_path_for("exercise_tags:list"),
        params={"searchString": "isometric"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == "isometric"


async def test_get_list_with_retired_exercise_tags(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_exercise_tag: None,
) -> None:
    response = await superuser_client.get(
        app.url_path_for("exercise_tags:list-with-retired"),
        params={"showOnlyRetired": True},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert all(item["deletedAt"] is not None for item in response_data)
    assert RETIRED_EXERCISE_TAG_NAME in {item["name"] for item in response_data}


# --- Get by ID ---


@pytest.mark.parametrize(
    ("tag_id", "status_code"),
    [
        pytest.param(1, status.HTTP_200_OK, id="active_item"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(RETIRED_EXERCISE_TAG_ID, status.HTTP_404_NOT_FOUND, id="retired_item_not_found"),
    ],
)
async def test_get_exercise_tag(
    app: FastAPI,
    user_client: AsyncClient,
    retired_exercise_tag: None,
    tag_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("exercise_tags:get", tag_id=tag_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == tag_id
        assert "deletedAt" not in response_data


# --- Update ---


async def test_update_exercise_tag(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercise_tags:update", tag_id=2),
        json={"name": "  OUTDOOR Updated  "},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == 2  # noqa: PLR2004
    assert response_data["name"] == "outdoor updated"


@pytest.mark.parametrize(
    ("tag_id", "payload", "status_code"),
    [
        pytest.param(2, {"name": "unilateral"}, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param(999, {"name": "not found"}, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(4, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_update_exercise_tag_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    tag_id: int,
    payload: dict[str, str | None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercise_tags:update", tag_id=tag_id),
        json=payload,
    )
    assert response.status_code == status_code


# --- Restore ---


@pytest.mark.parametrize(
    ("payload", "expected_name"),
    [
        pytest.param({}, RETIRED_EXERCISE_TAG_NAME, id="restored"),
        pytest.param(
            {"name": f"  {RETIRED_EXERCISE_TAG_NAME.upper()} "},
            RETIRED_EXERCISE_TAG_NAME,
            id="normalized_name_on_restore",
        ),
        pytest.param({"name": "medium impact"}, "medium impact", id="renamed_on_restore"),
    ],
)
async def test_restore_exercise_tag(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_exercise_tag: None,
    payload: dict[str, str],
    expected_name: str,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercise_tags:restore", tag_id=RETIRED_EXERCISE_TAG_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == RETIRED_EXERCISE_TAG_ID
    assert response_data["name"] == expected_name
    assert "deletedAt" not in response_data


@pytest.mark.parametrize(
    ("tag_id", "payload", "status_code"),
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
async def test_restore_exercise_tag_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    tag_id: int,
    payload: dict[str, None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercise_tags:restore", tag_id=tag_id),
        json=payload,
    )
    assert response.status_code == status_code


async def test_restore_exercise_tag_conflicts_when_name_retaken(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_exercise_tag: None,
) -> None:
    created = await superuser_client.post(
        app.url_path_for("exercise_tags:create"),
        json={"name": RETIRED_EXERCISE_TAG_NAME},
    )
    assert created.status_code == status.HTTP_201_CREATED

    restore = await superuser_client.patch(
        app.url_path_for("exercise_tags:restore", tag_id=RETIRED_EXERCISE_TAG_ID),
        json={},
    )
    assert restore.status_code == status.HTTP_409_CONFLICT


# --- Retire ---


@pytest.mark.parametrize(
    ("tag_id", "status_code"),
    [
        pytest.param(3, status.HTTP_204_NO_CONTENT, id="retired"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
    ],
)
async def test_delete_exercise_tag(
    app: FastAPI,
    superuser_client: AsyncClient,
    session: AsyncSession,
    tag_id: int,
    status_code: int,
) -> None:
    response = await superuser_client.delete(app.url_path_for("exercise_tags:delete", tag_id=tag_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_204_NO_CONTENT:
        stmt = select(Tag).where(Tag.id == tag_id).execution_options(include_deleted=True)
        retired_obj = await session.scalar(stmt)
        assert retired_obj is not None
        assert retired_obj.deleted_at is not None


# --- Access Control ---


@pytest.mark.parametrize(
    ("url_path", "method", "tag_id"),
    [
        ("exercise_tags:create", "post", None),
        ("exercise_tags:list-with-retired", "get", None),
        ("exercise_tags:update", "patch", 1),
        ("exercise_tags:restore", "patch", 1),
        ("exercise_tags:delete", "delete", 1),
    ],
)
async def test_regular_user_forbidden_on_exercise_tags(
    app: FastAPI,
    user_client: AsyncClient,
    url_path: str,
    method: str,
    tag_id: int | None,
) -> None:
    path_params = {"tag_id": tag_id} if tag_id is not None else {}
    response = await getattr(user_client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("url_path", "method", "tag_id"),
    [
        ("exercise_tags:create", "post", None),
        ("exercise_tags:list", "get", None),
        ("exercise_tags:list-with-retired", "get", None),
        ("exercise_tags:get", "get", 1),
        ("exercise_tags:update", "patch", 1),
        ("exercise_tags:restore", "patch", 1),
        ("exercise_tags:delete", "delete", 1),
    ],
)
async def test_tag_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    url_path: str,
    method: str,
    tag_id: int | None,
) -> None:
    path_params = {"tag_id": tag_id} if tag_id is not None else {}
    response = await getattr(client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
