from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import func, or_, select

from app.config.base import get_settings
from app.db.models.exercise import Exercise
from tests import constants as c
from tests.helpers import set_access_cookie

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.anyio

# --- Fixtures ---


@pytest.fixture(name="exercise_count")
async def fx_exercise_count(session: AsyncSession) -> Callable[[UUID, str], Awaitable[int]]:
    """Count seeded exercises per scope.

    system = system exercises; all = system and caller's own;
    user = caller's own. No scope ever counts another user's rows.
    """

    async def count(user_id: UUID, scope: str) -> int:
        model = Exercise
        stmt = select(func.count()).select_from(model)
        match scope:
            case "system":
                stmt = stmt.where(model.is_system_default.is_(True))
            case "user":
                stmt = stmt.where(model.created_by == user_id)
            case "all":
                stmt = stmt.where(or_(model.is_system_default.is_(True), model.created_by == user_id))
        result = await session.scalar(stmt)
        assert result is not None
        return result

    return count


# --- Create ---


@pytest.mark.parametrize(
    ("payload_type", "extra_data"),
    [
        ("minimal", {}),
        (
            "full",
            {
                "secondaryMuscles": [3, 4],
                "equipment": [7],
                "force": "push",
                "mechanic": "compound",
                "instructions": "Be strong.",
            },
        ),
    ],
)
async def test_create_exercise_success(
    app: FastAPI,
    user_client: AsyncClient,
    payload_type: str,
    extra_data: dict[str, Any],
) -> None:
    payload = {
        "name": f"Test Exercise {payload_type}",
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
        **extra_data,
    }

    response = await user_client.post(app.url_path_for("exercises:create"), json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert UUID(response_data["id"])
    assert response_data["name"] == payload["name"]
    assert {pr["id"] for pr in response_data["primaryMuscles"]} == {1}
    assert response_data["difficultyLevel"] == "beginner"
    assert response_data["category"] == "strength"

    if payload_type == "full":
        assert {sec["id"] for sec in response_data["secondaryMuscles"]} == {3, 4}
        assert {eq["id"] for eq in response_data["equipment"]} == {7}
        assert response_data["force"] == "push"
        assert response_data["mechanic"] == "compound"
        assert response_data["instructions"] == "Be strong."
    else:
        assert response_data["secondaryMuscles"] == []
        assert response_data["equipment"] == []
        assert response_data["force"] is None
        assert response_data["mechanic"] is None
        assert response_data["instructions"] is None


async def test_create_exercise_rejects_null_required_fields(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    invalid_payload = {
        "name": None,
        "difficultyLevel": None,
        "category": None,
        "primaryMuscles": [1],
    }
    response = await user_client.post(
        app.url_path_for("exercises:create"),
        json=invalid_payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"name", "difficultyLevel", "category"}


async def test_create_exercise_rejects_empty_primary_muscles(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    payload = {
        "name": "Test Exercise",
        "primaryMuscles": [],
        "difficultyLevel": "beginner",
        "category": "strength",
    }
    response = await user_client.post(app.url_path_for("exercises:create"), json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"primaryMuscles"}


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(c.USER_EXAMPLE_EXERCISE_NAME, id="exact"),
        pytest.param(c.USER_EXAMPLE_EXERCISE_NAME.lower(), id="case_folded"),
        pytest.param(c.USER_EXAMPLE_EXERCISE_NAME.replace(" ", "/"), id="slash"),
        pytest.param(c.USER_EXAMPLE_EXERCISE_NAME.replace(" ", "-"), id="dash"),
    ],
)
async def test_create_exercise_duplicate_name(
    app: FastAPI,
    user_client: AsyncClient,
    name: str,
) -> None:
    """A name that slugifies to an already-taken slug is rejected.

    Slugify folds case and punctuation, so spelling variants collide on the
    same slug as the exact duplicate.
    """
    payload = {
        "name": name,
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
    }
    response = await user_client.post(app.url_path_for("exercises:create"), json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("A" * 101, id="too_long"),
        pytest.param("AB", id="too_short"),
    ],
)
async def test_create_exercise_rejects_invalid_name_length(
    app: FastAPI,
    user_client: AsyncClient,
    name: str,
) -> None:
    response = await user_client.post(
        app.url_path_for("exercises:create"),
        json={
            "name": name,
            "primaryMuscles": [1],
            "difficultyLevel": "beginner",
            "category": "strength",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert "name" in error_fields


async def test_create_exercise_allows_same_name_for_another_user(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Exercise names are unique per owner, not globally."""
    payload = {
        "name": c.USER_EXAMPLE_EXERCISE_NAME,
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
    }
    set_access_cookie(
        client=client,
        user_id=c.ANOTHER_USER_ID,
        email=c.ANOTHER_USER_EMAIL,
    )
    response = await client.post(
        app.url_path_for("exercises:create"),
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == c.USER_EXAMPLE_EXERCISE_NAME


@pytest.mark.parametrize(
    ("patch_payload", "error_msg"),
    [
        pytest.param({"primaryMuscles": [99]}, "Muscle group", id="muscle_primary"),
        pytest.param({"secondaryMuscles": [99]}, "Muscle group", id="muscle_secondary"),
        pytest.param({"equipment": [99]}, "Equipment", id="equipment"),
        pytest.param({"tags": [99]}, "Tag", id="tag"),
    ],
)
async def test_create_system_exercise_unknown_catalog_ids(
    app: FastAPI,
    superuser_client: AsyncClient,
    patch_payload: dict[str, list[int]],
    error_msg: str,
) -> None:
    """Unknown catalog ids are rejected with 404 listing the missing ids.

    Ids are resolved by the service, not the schema, so field validation cannot
    catch them.
    """
    required_fields = {
        "name": "Test Exercise",
        "difficultyLevel": "beginner",
        "category": "strength",
        "instructions": "Be strong.",
        "imageStartPath": "/elite-bench-press/start.jpg",
        "imageEndPath": "/elite-bench-press/end.jpg",
        "primaryMuscles": [1],
        "secondaryMuscles": [2],
        "equipment": [1],
        "tags": [1],
        **patch_payload,
    }
    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=required_fields,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert error_msg in response.json()["message"]
    assert response.json()["details"]["missing_ids"] == [99]


async def test_create_system_exercise_success(
    app: FastAPI,
    superuser_client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Image paths are stored relative and prefixed only at render time."""
    payload = {
        "name": "Elite Bench Press",
        "primaryMuscles": [1],
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": "Professional form only.",
        "tags": [1],
        "imageStartPath": "/elite-bench-press/start.jpg",
        "imageEndPath": "/elite-bench-press/end.jpg",
    }
    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["name"] == payload["name"]
    assert response_data["createdBy"] is None
    assert {t["id"] for t in response_data["tags"]} == {1}

    cdn_prefix = get_settings().app.cdn_images_url_prefix
    assert response_data["imageStartPath"] == f"{cdn_prefix}/elite-bench-press/start.jpg"
    assert response_data["imageEndPath"] == f"{cdn_prefix}/elite-bench-press/end.jpg"

    db_obj = cast("Exercise", await session.get(Exercise, UUID(response_data["id"])))
    assert db_obj.image_start_path == "/elite-bench-press/start.jpg"
    assert db_obj.image_end_path == "/elite-bench-press/end.jpg"


async def test_create_system_exercise_rejects_null_required_fields(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    payload = {
        "name": "Elite Bench Press",
        "primaryMuscles": [1],
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": None,
        "imageStartPath": None,
        "imageEndPath": None,
        "tags": [1],
    }
    response = await superuser_client.post(app.url_path_for("exercises:create-system"), json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"instructions", "imageStartPath", "imageEndPath"}


async def test_create_system_exercise_rejects_empty_tags(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    payload = {
        "name": "Elite Bench Press",
        "primaryMuscles": [1],
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": "Be strong.",
        "imageStartPath": "/elite-bench-press/start.jpg",
        "imageEndPath": "/elite-bench-press/end.jpg",
        "tags": [],
    }
    response = await superuser_client.post(app.url_path_for("exercises:create-system"), json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"tags"}


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(c.SYSTEM_EXERCISE_NAME, id="exact"),
        pytest.param(c.SYSTEM_EXERCISE_NAME.lower(), id="case_folded"),
        pytest.param(c.SYSTEM_EXERCISE_NAME.replace(" ", "/"), id="slash"),
        pytest.param(c.SYSTEM_EXERCISE_NAME.replace(" ", "-"), id="dash"),
    ],
)
async def test_create_system_exercise_duplicate_name(
    app: FastAPI,
    superuser_client: AsyncClient,
    name: str,
) -> None:
    """A system name that slugifies to an existing system slug is rejected.

    System uniqueness is global (uidx_exercise_system), unlike the per-owner
    index for user exercises.
    """
    payload = {
        "name": name,
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
        "instructions": "Be strong.",
        "tags": [1],
        "imageStartPath": "/trail-running-walking/0.jpg",
        "imageEndPath": "/trail-running-walking/1.jpg",
    }
    response = await superuser_client.post(app.url_path_for("exercises:create-system"), json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    ("image_path", "is_valid"),
    [
        pytest.param("/bench-press/1.jpg", True, id="single_segment"),
        pytest.param("/bench-press-v2/start-image.png", True, id="multi_dash_segment"),
        pytest.param("/underscore_v1/dash-v2.jpeg", False, id="error_underscore_in_segment"),
        pytest.param("no-leading-slash.jpg", False, id="error_no_leading_slash"),
        pytest.param("/wrong-extension.gif", False, id="error_bad_extension"),
    ],
)
@pytest.mark.parametrize("target", ["create", "update"])
async def test_system_exercise_image_paths(
    app: FastAPI,
    superuser_client: AsyncClient,
    image_path: str,
    is_valid: bool,
    target: str,
) -> None:
    """The CDN path contract holds on both system-exercise write routes."""
    if target == "create":
        payload = {
            "name": "Elite Bench Press",
            "primaryMuscles": [1],
            "difficultyLevel": "expert",
            "category": "strength",
            "instructions": "Professional form only.",
            "tags": [1],
            "imageStartPath": image_path,
            "imageEndPath": image_path,
        }
        ok_status = status.HTTP_201_CREATED
        response = await superuser_client.post(
            app.url_path_for("exercises:create-system"),
            json=payload,
        )
    else:
        payload = {"imageStartPath": image_path, "imageEndPath": image_path}
        ok_status = status.HTTP_200_OK
        response = await superuser_client.patch(
            app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
            json=payload,
        )

    if is_valid:
        assert response.status_code == ok_status
        return
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_detail = {f["field"] for f in response.json()["details"]}
    assert {"imageStartPath", "imageEndPath"} == error_detail


# --- List Exercises ---


@pytest.mark.parametrize("scope", ["all", "user", "system"])
async def test_list_exercises_scopes(
    app: FastAPI,
    user_client: AsyncClient,
    exercise_count: Callable[[UUID, str], Awaitable[int]],
    scope: str,
) -> None:
    """Each scope returns only what is visible to the caller.

    user = the caller's own rows, so another user's seeded exercise must
    never appear; all = system and the caller's own.
    """
    response = await user_client.get(
        app.url_path_for("exercises:list"),
        params={"scope": scope},
    )
    assert response.status_code == status.HTTP_200_OK
    assert int(response.json()["total"]) == await exercise_count(c.USER_EXAMPLE_ID, scope)


async def test_list_system_exercises_as_superuser(
    app: FastAPI,
    superuser_client: AsyncClient,
    exercise_count: Callable[[UUID, str], Awaitable[int]],
) -> None:
    """A superuser may list system exercises.

    Read routes stay open to the superuser role (unlike the write routes), so
    this pins the open half of the admin access contract.
    """
    response = await superuser_client.get(
        app.url_path_for("exercises:list"),
        params={"scope": "system"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert int(response.json()["total"]) == await exercise_count(c.SUPERUSER_ID, "system")


@pytest.mark.parametrize(
    ("query_params", "expected_count"),
    [
        pytest.param({"scope": "system", "searchString": " Upright Row "}, 1, id="search_system"),
        pytest.param({"scope": "user", "searchString": "Exercise Two"}, 1, id="search_user"),
        pytest.param({"scope": "all", "category": "strength"}, 9, id="category"),
        pytest.param({"scope": "all", "difficultyLevel": "expert"}, 0, id="difficulty_expert_none"),
        pytest.param({"scope": "system", "difficultyLevel": "beginner"}, 6, id="difficulty_beginner_system"),
    ],
)
async def test_list_exercises_filters(
    app: FastAPI,
    user_client: AsyncClient,
    query_params: dict[str, str],
    expected_count: int,
) -> None:
    """Scalar filters narrow the page; expected counts are seed-derived."""
    response = await user_client.get(
        app.url_path_for("exercises:list"),
        params=query_params,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["total"] == expected_count


@pytest.mark.parametrize(
    ("query_params", "expected_count"),
    [
        pytest.param({"primaryMuscles": [1, 12], "scope": "user"}, 2, id="primary"),
        pytest.param({"primaryMuscles": [2], "scope": "user"}, 0, id="primary_role"),
        pytest.param({"secondaryMuscles": [2, 5], "scope": "user"}, 2, id="secondary"),
        pytest.param({"primaryMuscles": [1], "secondaryMuscles": [2], "scope": "user"}, 1, id="both_roles"),
        pytest.param({"equipment": [2, 7], "scope": "user"}, 2, id="equipment"),
        pytest.param({"tags": [1, 2], "scope": "user"}, 0, id="tags_absent_on_custom"),
        pytest.param({"tags": [1, 2], "scope": "system"}, 11, id="tags_system"),
    ],
)
async def test_list_exercises_m2m_filters(
    app: FastAPI,
    user_client: AsyncClient,
    query_params: dict[str, Any],
    expected_count: int,
) -> None:
    """Relationship filters narrow the page; expected counts are seed-derived.

    Muscle role is part of the match: muscle 2 exists only as a secondary muscle,
    so a primary-muscles filter on it correctly yields zero.
    """
    response = await user_client.get(
        app.url_path_for("exercises:list"),
        params=query_params,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["total"] == expected_count


async def test_list_exercises_cache_is_isolated_per_user(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """A cached page is keyed per user and reused verbatim on a repeat.

    The page key includes user_id, and the autouse cache reset runs only
    between tests, so all requests below share one cache. Without the
    user_id suffix the second caller would receive the first caller's
    rows; the final request is a repeat of the first one, which pins the
    cache-hit return path and proves the isolation left the first
    caller's key intact.
    """
    set_access_cookie(client, c.USER_EXAMPLE_ID, c.USER_EXAMPLE_EMAIL)
    first = await client.get(
        app.url_path_for("exercises:list"),
        params={"scope": "user"},
    )
    assert first.status_code == status.HTTP_200_OK
    assert int(first.json()["total"]) > 0

    set_access_cookie(client, c.ANOTHER_USER_ID, c.ANOTHER_USER_EMAIL)
    second = await client.get(
        app.url_path_for("exercises:list"),
        params={"scope": "user"},
    )
    exercise_ids = {item["id"] for item in second.json()["items"]}
    assert second.status_code == status.HTTP_200_OK
    assert str(c.ANOTHER_USER_EXERCISE_ID) in exercise_ids

    set_access_cookie(client, c.USER_EXAMPLE_ID, c.USER_EXAMPLE_EMAIL)
    repeat = await client.get(
        app.url_path_for("exercises:list"),
        params={"scope": "user"},
    )
    assert repeat.status_code == status.HTTP_200_OK
    assert repeat.json() == first.json()


# --- Get Exercise by ID and Look Up by Name ---


@pytest.mark.parametrize(
    ("exercise_id", "status_code"),
    [
        pytest.param(c.USER_EXAMPLE_EXERCISE_ID, status.HTTP_200_OK, id="own"),
        pytest.param(c.SYSTEM_EXERCISE_ID, status.HTTP_200_OK, id="system"),
        pytest.param(UUID("019d1c19-0d28-7e62-a4ab-052011e5f48c"), status.HTTP_404_NOT_FOUND, id="missing"),
        pytest.param(c.ANOTHER_USER_EXERCISE_ID, status.HTTP_403_FORBIDDEN, id="another_user"),
    ],
)
async def test_get_exercise(
    app: FastAPI,
    user_client: AsyncClient,
    exercise_id: UUID,
    status_code: int,
) -> None:
    """Access resolves to system exercises or the caller's own rows.

    Anything else is hidden: another user's row answers 403, a missing id 404.
    """
    response = await user_client.get(
        app.url_path_for("exercises:get", exercise_id=exercise_id),
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        assert response.json()["id"] == str(exercise_id)


async def test_get_system_exercise_as_superuser(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """A superuser may read a system exercise.

    Read routes stay open to the superuser role (unlike the write routes), so
    this pins the open half of the admin access contract.
    """
    response = await superuser_client.get(
        app.url_path_for("exercises:get", exercise_id=c.SYSTEM_EXERCISE_ID),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(c.SYSTEM_EXERCISE_ID)


@pytest.mark.parametrize(
    ("scope", "name", "expected_name", "status_code"),
    [
        pytest.param("user", c.USER_EXAMPLE_EXERCISE_NAME, c.USER_EXAMPLE_EXERCISE_NAME, status.HTTP_200_OK, id="own"),
        pytest.param("user", c.ANOTHER_USER_EXERCISE_NAME, None, status.HTTP_404_NOT_FOUND, id="another_user"),
        pytest.param("system", c.SYSTEM_EXERCISE_NAME, c.SYSTEM_EXERCISE_NAME, status.HTTP_200_OK, id="system"),
        pytest.param(
            "user",
            f"  {c.USER_EXAMPLE_EXERCISE_NAME.lower()}  ",
            c.USER_EXAMPLE_EXERCISE_NAME,
            status.HTTP_200_OK,
            id="slug_normalization",
        ),
    ],
)
async def test_lookup_exercise(
    app: FastAPI,
    user_client: AsyncClient,
    scope: str,
    name: str,
    expected_name: str | None,
    status_code: int,
) -> None:
    """Lookup resolves by slugified name inside the caller's scope.

    The same exercise is reachable through spelling variants of its name;
    another user's row is not reachable through the user scope.
    """
    response = await user_client.get(
        app.url_path_for("exercises:lookup"),
        params={"scope": scope, "name": name},
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["name"] == expected_name


async def test_lookup_system_exercise_as_superuser(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """Lookup resolves system content for a superuser.

    Read routes stay open to the superuser role (unlike the write routes), so
    this pins the open half of the admin access contract.
    """
    response = await superuser_client.get(
        app.url_path_for("exercises:lookup"),
        params={"scope": "system", "name": c.SYSTEM_EXERCISE_NAME},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == c.SYSTEM_EXERCISE_NAME


# --- Update ---


async def test_update_exercise_success(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    payload = {
        "name": "Renamed Exercise",
        "primaryMuscles": [4, 8],
        "secondaryMuscles": [5, 10],
        "force": "push",
        "difficultyLevel": "expert",
        "mechanic": "compound",
        "equipment": [7],
        "category": "powerlifting",
        "instructions": "Updated instructions.",
    }
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=c.USER_EXAMPLE_EXERCISE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == payload["name"]
    assert {pr["id"] for pr in response_data["primaryMuscles"]} == {4, 8}
    assert {sec["id"] for sec in response_data["secondaryMuscles"]} == {5, 10}
    assert response_data["force"] == "push"
    assert response_data["difficultyLevel"] == "expert"
    assert response_data["mechanic"] == "compound"
    assert {eq["id"] for eq in response_data["equipment"]} == {7}
    assert response_data["category"] == "powerlifting"
    assert response_data["instructions"] == payload["instructions"]
    assert response_data["createdBy"] == str(c.USER_EXAMPLE_ID)


@pytest.mark.parametrize(
    ("exercise_id", "data", "status_code"),
    [
        pytest.param(c.ANOTHER_USER_EXERCISE_ID, {}, status.HTTP_404_NOT_FOUND, id="another_user"),
        pytest.param(
            c.USER_EXAMPLE_EXERCISE_ID,
            {"name": c.USER_EXAMPLE_EXERCISE_NAME_TWO},
            status.HTTP_409_CONFLICT,
            id="duplicate_name",
        ),
    ],
)
async def test_update_exercise_negative_cases(
    app: FastAPI,
    user_client: AsyncClient,
    exercise_id: UUID,
    data: dict[str, str],
    status_code: int,
) -> None:
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=exercise_id),
        json=data,
    )
    assert response.status_code == status_code


async def test_update_exercise_switches_muscle_role(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    """Swapping the role of a muscle updates the junction row.

    ExerciseMuscle excludes the role from its primary key, so a muscle cannot be
    both primary and secondary. Moving one across roles must rewrite the row
    rather than append a second one.
    """
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=c.USER_EXAMPLE_EXERCISE_ID),
        json={"primaryMuscles": [2], "secondaryMuscles": [1]},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert {pr["id"] for pr in response_data["primaryMuscles"]} == {2}
    assert {sec["id"] for sec in response_data["secondaryMuscles"]} == {1}


async def test_update_exercise_rejects_duplicate_muscle_role(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=c.USER_EXAMPLE_EXERCISE_ID),
        json={"primaryMuscles": [1], "secondaryMuscles": [1, 2]},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["details"] == {"group_ids": [1]}


async def test_update_system_exercise_success(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    payload = {
        "name": "Elite Bench Press",
        "primaryMuscles": [1, 3],
        "secondaryMuscles": [5, 6],
        "force": "push",
        "difficultyLevel": "expert",
        "mechanic": "compound",
        "equipment": [2, 7],
        "category": "strength",
        "instructions": "Short instructions.",
        "imageStartPath": "/elite-bench-press/start.jpg",
        "imageEndPath": "/elite-bench-press/end.jpg",
        "tags": [1, 2],
    }
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(c.SYSTEM_EXERCISE_ID)
    assert response_data["name"] == payload["name"]
    assert {pr["id"] for pr in response_data["primaryMuscles"]} == {1, 3}
    assert {sec["id"] for sec in response_data["secondaryMuscles"]} == {5, 6}
    assert {eq["id"] for eq in response_data["equipment"]} == {2, 7}
    assert {t["id"] for t in response_data["tags"]} == {1, 2}
    assert response_data["imageStartPath"].endswith("/elite-bench-press/start.jpg")
    assert response_data["imageEndPath"].endswith("/elite-bench-press/end.jpg")
    assert response_data["createdBy"] is None


async def test_update_system_exercise_clears_empty_lists(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """An explicit empty list clears the relationship.

    Relationships corresponding to omitted keys remain unchanged.
    """
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json={"secondaryMuscles": [], "equipment": []},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["secondaryMuscles"] == []
    assert response_data["equipment"] == []
    assert {pr["id"] for pr in response_data["primaryMuscles"]} == {4}
    assert {t["id"] for t in response_data["tags"]} == {2, 5}


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"primaryMuscles": [99]}, id="muscle_primary"),
        pytest.param({"secondaryMuscles": [99]}, id="muscle_secondary"),
    ],
)
async def test_update_system_exercise_unknown_muscle_ids(
    app: FastAPI,
    superuser_client: AsyncClient,
    payload: dict[str, Any],
) -> None:
    """Unknown muscle ids are rejected on update too.

    Unlike create, update resolves muscles inside the junction merge, so the
    404 must survive the pop-and-merge plumbing of the update() override.
    """
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Muscle group" in response.json()["message"]
    assert response.json()["details"]["missing_ids"] == [99]


@pytest.mark.parametrize(
    ("exercise_id", "data", "status_code"),
    [
        pytest.param(UUID("019d1c19-0d25-7633-8fc0-bbfa290e5088"), {}, status.HTTP_404_NOT_FOUND, id="missing"),
        pytest.param(
            c.SYSTEM_EXERCISE_ID,
            {"name": c.SYSTEM_EXERCISE_NAME_TWO.replace("-", "/")},
            status.HTTP_409_CONFLICT,
            id="duplicate_name",
        ),
        pytest.param(c.SYSTEM_EXERCISE_ID, {"tags": []}, status.HTTP_422_UNPROCESSABLE_CONTENT, id="empty_tags"),
    ],
)
async def test_update_system_exercise_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    exercise_id: UUID,
    data: dict[str, Any],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=exercise_id),
        json=data,
    )
    assert response.status_code == status_code


# --- Delete ---


@pytest.mark.parametrize(
    ("exercise_id", "status_code"),
    [
        pytest.param(c.USER_EXAMPLE_EXERCISE_ID, status.HTTP_204_NO_CONTENT, id="own"),
        pytest.param(c.SYSTEM_EXERCISE_ID, status.HTTP_403_FORBIDDEN, id="system"),
        pytest.param(c.ANOTHER_USER_EXERCISE_ID, status.HTTP_403_FORBIDDEN, id="another_user"),
        pytest.param(UUID("019d1c19-0d26-7330-b1af-91601739d0cd"), status.HTTP_404_NOT_FOUND, id="missing"),
    ],
)
async def test_delete_exercise(
    app: FastAPI,
    user_client: AsyncClient,
    exercise_id: UUID,
    status_code: int,
) -> None:
    response = await user_client.delete(app.url_path_for("exercises:delete", exercise_id=exercise_id))
    assert response.status_code == status_code
    if status_code == status.HTTP_204_NO_CONTENT:
        response = await user_client.get(app.url_path_for("exercises:get", exercise_id=exercise_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Access Control ---


@pytest.mark.parametrize(
    ("url_path", "method", "exercise_id"),
    [
        pytest.param("exercises:create", "post", None, id="create"),
        pytest.param("exercises:update", "patch", c.USER_EXAMPLE_EXERCISE_ID, id="update"),
        pytest.param("exercises:delete", "delete", c.USER_EXAMPLE_EXERCISE_ID, id="delete"),
    ],
)
async def test_superuser_forbidden_on_user_exercises(
    app: FastAPI,
    superuser_client: AsyncClient,
    url_path: str,
    method: str,
    exercise_id: UUID | None,
) -> None:
    path_params = {"exercise_id": exercise_id} if exercise_id is not None else {}
    response = await getattr(superuser_client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("url_path", "method", "exercise_id"),
    [
        pytest.param("exercises:create-system", "post", None, id="create_system"),
        pytest.param("exercises:update-system", "patch", c.SYSTEM_EXERCISE_ID, id="update_system"),
    ],
)
async def test_regular_user_forbidden_on_system_exercises(
    app: FastAPI,
    user_client: AsyncClient,
    url_path: str,
    method: str,
    exercise_id: UUID | None,
) -> None:
    path_params = {"exercise_id": exercise_id} if exercise_id is not None else {}
    response = await getattr(user_client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("url_path", "method", "exercise_id"),
    [
        pytest.param("exercises:create", "post", None, id="create"),
        pytest.param("exercises:create-system", "post", None, id="create_system"),
        pytest.param("exercises:list", "get", None, id="list"),
        pytest.param("exercises:lookup", "get", None, id="lookup"),
        pytest.param("exercises:get", "get", c.USER_EXAMPLE_EXERCISE_ID, id="get"),
        pytest.param("exercises:update", "patch", c.USER_EXAMPLE_EXERCISE_ID, id="update"),
        pytest.param("exercises:update-system", "patch", c.SYSTEM_EXERCISE_ID, id="update_system"),
        pytest.param("exercises:delete", "delete", c.USER_EXAMPLE_EXERCISE_ID, id="delete"),
    ],
)
async def test_exercise_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    url_path: str,
    method: str,
    exercise_id: UUID | None,
) -> None:
    path_params = {"exercise_id": exercise_id} if exercise_id is not None else {}
    response = await getattr(client, method)(app.url_path_for(url_path, **path_params))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
