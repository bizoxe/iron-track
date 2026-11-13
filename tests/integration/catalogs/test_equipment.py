"""Representative suite for the catalog trio.

Pins, once, the depth shared by all catalogs: soft-delete visibility
(what active reads hide, what the admin listing reveals, repeated retire),
the partial unique index (freed names), filter semantics
(ordering, search, showOnlyRetired), and cache mechanics (stale serving,
per-mutation invalidation).

Also pins this router's own surface — routes, schema signatures,
access control, and the unique index (duplicate names, retaken restores)
— the surface test_exercise_tags.py and test_muscle_groups.py mirror
for their own routers and tables.

Schema boundaries (name lengths, cache-key structure) live in the unit tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from fastapi import status
from sqlalchemy import func, select, text, update

from app.db.models.catalog import Equipment

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.anyio


RETIRED_EQUIPMENT_ID = 13
RETIRED_EQUIPMENT_NAME = "trx"

# --- Fixtures ---


@pytest.fixture(name="retired_equipment")
async def fx_seed_retired_equipment(session: AsyncSession) -> None:
    session.add(
        Equipment(id=RETIRED_EQUIPMENT_ID, name=RETIRED_EQUIPMENT_NAME, deleted_at=datetime.now(tz=UTC)),
    )
    await session.flush()
    # Keep the identity sequence past any explicitly seeded id (same trick
    # as the seeder): otherwise a later nextval() can collide with this row.
    await session.execute(
        text(
            f"SELECT setval(pg_get_serial_sequence('{Equipment.__tablename__}', 'id'), "
            f"greatest(nextval(pg_get_serial_sequence('{Equipment.__tablename__}', 'id')), {RETIRED_EQUIPMENT_ID}))",
        ),
    )


# --- Create ---


@pytest.mark.parametrize(
    ("payload", "result", "status_code"),
    [
        pytest.param(
            {"name": "  Weighted   Vest  "},
            "weighted vest",
            status.HTTP_201_CREATED,
            id="name_normalized_on_save",
        ),
        pytest.param({"name": "body only"}, None, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_create_equipment(
    app: FastAPI,
    superuser_client: AsyncClient,
    payload: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json=payload,
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


# --- List Equipment ---


async def test_get_list_equipment_returns_active_only(
    app: FastAPI,
    user_client: AsyncClient,
    session: AsyncSession,
) -> None:
    all_active_count = await session.scalar(select(func.count()).where(Equipment.deleted_at.is_(None)))
    response = await user_client.get(app.url_path_for("equipment:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) == all_active_count
    assert all("deletedAt" not in item for item in response_data)


@pytest.mark.parametrize(
    ("params", "expected_name"),
    [
        pytest.param({}, "bands", id="default_order_by_name_asc"),
        pytest.param({"sortOrder": "desc"}, "other", id="order_by_name_desc"),
        pytest.param({"orderBy": "id", "sortOrder": "desc"}, "e-z curl bar", id="order_by_id_desc"),
    ],
)
async def test_get_list_equipment_ordering(
    app: FastAPI,
    user_client: AsyncClient,
    params: dict[str, str],
    expected_name: str,
) -> None:
    response = await user_client.get(app.url_path_for("equipment:list"), params=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == expected_name


@pytest.mark.parametrize(
    ("params", "expected_name"),
    [
        pytest.param({"searchString": "barbell"}, "barbell", id="exact_match"),
        pytest.param({"searchString": "ca"}, "cable", id="partial_match"),
        pytest.param({"searchString": "BARBELL"}, "barbell", id="case_insensitive"),
    ],
)
async def test_get_list_equipment_search(
    app: FastAPI,
    user_client: AsyncClient,
    params: dict[str, str],
    expected_name: str,
) -> None:
    response = await user_client.get(
        app.url_path_for("equipment:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["name"] == expected_name


async def test_get_list_with_retired_equipment(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_equipment: None,
    session: AsyncSession,
) -> None:
    """The admin listing returns the full table; the slice only retired rows."""
    stmt = select(func.count()).select_from(Equipment).execution_options(include_deleted=True)
    all_items_count = await session.scalar(stmt)
    response = await superuser_client.get(app.url_path_for("equipment:list-with-retired"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == all_items_count

    expected_retired_count = await session.scalar(select(func.count()).where(Equipment.deleted_at.is_not(None)))
    retired_only = await superuser_client.get(
        app.url_path_for("equipment:list-with-retired"),
        params={"showOnlyRetired": True},
    )
    assert retired_only.status_code == status.HTTP_200_OK
    retired_only_data = retired_only.json()
    assert len(retired_only_data) == expected_retired_count
    assert all(item["deletedAt"] is not None for item in retired_only_data)
    assert RETIRED_EQUIPMENT_NAME in {item["name"] for item in retired_only_data}


# --- Get by ID ---


@pytest.mark.parametrize(
    ("equipment_id", "status_code"),
    [
        pytest.param(1, status.HTTP_200_OK, id="active_item"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(RETIRED_EQUIPMENT_ID, status.HTTP_404_NOT_FOUND, id="retired_item_not_found"),
    ],
)
async def test_get_equipment(
    app: FastAPI,
    user_client: AsyncClient,
    retired_equipment: None,
    equipment_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("equipment:get", equipment_id=equipment_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == equipment_id
        assert "deletedAt" not in response_data


# --- Update ---


async def test_update_equipment(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("equipment:update", equipment_id=6),
        json={"name": "  DUMBBELL Updated  "},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == 6  # noqa: PLR2004
    assert response_data["name"] == "dumbbell updated"


@pytest.mark.parametrize(
    ("equipment_id", "payload", "status_code"),
    [
        pytest.param(2, {"name": "barbell"}, status.HTTP_409_CONFLICT, id="duplicate_name"),
        pytest.param(999, {"name": "not found"}, status.HTTP_404_NOT_FOUND, id="item_not_found"),
        pytest.param(5, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_update_equipment_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    equipment_id: int,
    payload: dict[str, str | None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("equipment:update", equipment_id=equipment_id),
        json=payload,
    )
    assert response.status_code == status_code


# --- Restore ---


@pytest.mark.parametrize(
    ("payload", "expected_name"),
    [
        pytest.param({}, RETIRED_EQUIPMENT_NAME, id="restored"),
        pytest.param(
            {"name": f"  {RETIRED_EQUIPMENT_NAME.upper()} "},
            RETIRED_EQUIPMENT_NAME,
            id="normalized_name_on_restore",
        ),
        pytest.param({"name": "trx pro"}, "trx pro", id="renamed_on_restore"),
    ],
)
async def test_restore_equipment(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_equipment: None,
    payload: dict[str, str],
    expected_name: str,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("equipment:restore", equipment_id=RETIRED_EQUIPMENT_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == RETIRED_EQUIPMENT_ID
    assert response_data["name"] == expected_name
    assert "deletedAt" not in response_data


@pytest.mark.parametrize(
    ("equipment_id", "payload", "status_code"),
    [
        pytest.param(999, {}, status.HTTP_404_NOT_FOUND, id="not_found"),
        pytest.param(1, {}, status.HTTP_409_CONFLICT, id="rejects_active_item"),
        pytest.param(4, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT, id="name_rejects_null"),
    ],
)
async def test_restore_equipment_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    equipment_id: int,
    payload: dict[str, None],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("equipment:restore", equipment_id=equipment_id),
        json=payload,
    )
    assert response.status_code == status_code


async def test_restore_equipment_conflicts_when_name_retaken(
    app: FastAPI,
    superuser_client: AsyncClient,
    retired_equipment: None,
) -> None:
    """A restore must not silently shadow the active holder of the name."""
    created = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": RETIRED_EQUIPMENT_NAME},
    )
    assert created.status_code == status.HTTP_201_CREATED

    restore = await superuser_client.patch(
        app.url_path_for("equipment:restore", equipment_id=RETIRED_EQUIPMENT_ID),
        json={},
    )
    assert restore.status_code == status.HTTP_409_CONFLICT


# --- Retire ---


@pytest.mark.parametrize(
    ("equipment_id", "status_code"),
    [
        pytest.param(3, status.HTTP_204_NO_CONTENT, id="retired"),
        pytest.param(999, status.HTTP_404_NOT_FOUND, id="item_not_found"),
    ],
)
async def test_delete_equipment(
    app: FastAPI,
    superuser_client: AsyncClient,
    session: AsyncSession,
    equipment_id: int,
    status_code: int,
) -> None:
    response = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=equipment_id),
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_204_NO_CONTENT:
        stmt = select(Equipment).where(Equipment.id == equipment_id).execution_options(include_deleted=True)
        retired_obj = await session.scalar(stmt)
        assert retired_obj is not None
        assert retired_obj.deleted_at is not None


async def test_delete_equipment_frees_name_for_reuse(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """The unique index covers active rows only; retired names can be reused."""
    created = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": "Freed Name Probe"},
    )
    assert created.status_code == status.HTTP_201_CREATED

    deleted = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=created.json()["id"]),
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    reused = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": "Freed Name Probe"},
    )
    assert reused.status_code == status.HTTP_201_CREATED


async def test_delete_equipment_twice_returns_not_found(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """Repeated retire returns 404, not 204: soft-deleted rows are invisible."""
    created = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": "Retire Twice Probe"},
    )
    assert created.status_code == status.HTTP_201_CREATED

    first = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=created.json()["id"]),
    )
    assert first.status_code == status.HTTP_204_NO_CONTENT

    second = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=created.json()["id"]),
    )
    assert second.status_code == status.HTTP_404_NOT_FOUND


# --- Cache ---


async def test_list_serves_cache_until_mutation_invalidates_it(
    app: FastAPI,
    user_client: AsyncClient,
    superuser_client: AsyncClient,
    session: AsyncSession,
) -> None:
    """The list serves cached data until a mutation invalidates it.

    Direct DB updates remain invisible to the list endpoint until an API
    mutation invalidates the cache.
    """
    created = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": "cache probe one"},
    )
    assert created.status_code == status.HTTP_201_CREATED
    equipment_id = created.json()["id"]

    first = await user_client.get(app.url_path_for("equipment:list"))
    assert first.status_code == status.HTTP_200_OK
    assert "cache probe one" in {item["name"] for item in first.json()}

    # Rewrite the row behind the API's back: same transaction, no invalidation.
    await session.execute(
        update(Equipment).where(Equipment.id == equipment_id).values(name="cache probe two"),
    )
    # Drop identity-map copies: the next read must reflect the database, not memory.
    session.expire_all()

    stale = await user_client.get(app.url_path_for("equipment:list"))
    assert stale.status_code == status.HTTP_200_OK
    assert "cache probe one" in {item["name"] for item in stale.json()}
    assert "cache probe two" not in {item["name"] for item in stale.json()}

    renamed = await superuser_client.patch(
        app.url_path_for("equipment:update", equipment_id=equipment_id),
        json={"name": "cache probe three"},
    )
    assert renamed.status_code == status.HTTP_200_OK

    fresh = await user_client.get(app.url_path_for("equipment:list"))
    assert "cache probe three" in {item["name"] for item in fresh.json()}


async def test_mutations_invalidate_cached_listings(
    app: FastAPI,
    user_client: AsyncClient,
    superuser_client: AsyncClient,
) -> None:
    """Every mutation drops the whole table's listing cache, not one key.

    Each trailing GET both checks the mutation's effect and warms the cache
    for the next step, so the chain proves invalidation per method.
    """
    base_warm = await user_client.get(app.url_path_for("equipment:list"))
    assert base_warm.status_code == status.HTTP_200_OK
    search_warm = await user_client.get(
        app.url_path_for("equipment:list"),
        params={"searchString": "lifecycle"},
    )
    assert search_warm.json() == []

    created = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json={"name": "lifecycle probe"},
    )
    assert created.status_code == status.HTTP_201_CREATED
    equipment_id = created.json()["id"]

    base_after_create = await user_client.get(app.url_path_for("equipment:list"))
    assert "lifecycle probe" in {i["name"] for i in base_after_create.json()}
    search_after_create = await user_client.get(
        app.url_path_for("equipment:list"),
        params={"searchString": "lifecycle"},
    )
    assert {i["name"] for i in search_after_create.json()} == {"lifecycle probe"}

    renamed = await superuser_client.patch(
        app.url_path_for("equipment:update", equipment_id=equipment_id),
        json={"name": "lifecycle probe two"},
    )
    assert renamed.status_code == status.HTTP_200_OK
    names = {i["name"] for i in (await user_client.get(app.url_path_for("equipment:list"))).json()}
    assert "lifecycle probe" not in names
    assert "lifecycle probe two" in names

    retired = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=equipment_id),
    )
    assert retired.status_code == status.HTTP_204_NO_CONTENT
    names = {i["name"] for i in (await user_client.get(app.url_path_for("equipment:list"))).json()}
    assert "lifecycle probe two" not in names

    restored = await superuser_client.patch(
        app.url_path_for("equipment:restore", equipment_id=equipment_id),
        json={},
    )
    assert restored.status_code == status.HTTP_200_OK
    names = {i["name"] for i in (await user_client.get(app.url_path_for("equipment:list"))).json()}
    assert "lifecycle probe two" in names


# --- Access Control ---


@pytest.mark.parametrize(
    ("url_path", "method", "equipment_id"),
    [
        ("equipment:create", "post", None),
        ("equipment:list-with-retired", "get", None),
        ("equipment:update", "patch", 1),
        ("equipment:restore", "patch", 1),
        ("equipment:delete", "delete", 1),
    ],
)
async def test_regular_user_forbidden_on_equipment(
    app: FastAPI,
    user_client: AsyncClient,
    url_path: str,
    method: str,
    equipment_id: int | None,
) -> None:
    path_params = {"equipment_id": equipment_id} if equipment_id is not None else {}
    response = await getattr(user_client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("url_path", "method", "equipment_id"),
    [
        ("equipment:create", "post", None),
        ("equipment:list", "get", None),
        ("equipment:list-with-retired", "get", None),
        ("equipment:get", "get", 1),
        ("equipment:update", "patch", 1),
        ("equipment:restore", "patch", 1),
        ("equipment:delete", "delete", 1),
    ],
)
async def test_equipment_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    url_path: str,
    method: str,
    equipment_id: int | None,
) -> None:
    path_params = {"equipment_id": equipment_id} if equipment_id is not None else {}
    response = await getattr(client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
