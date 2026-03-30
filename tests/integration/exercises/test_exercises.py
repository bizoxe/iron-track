from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest
from fastapi import status

from app.domain.exercises.schemas import slugify
from tests import constants as c

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import FastAPI
    from httpx import AsyncClient


pytestmark = pytest.mark.anyio

# --- CREATE TESTS ---


@pytest.mark.parametrize(
    ("payload_type", "extra_data"),
    [
        ("minimal", {}),
        (
            "full",
            {
                "secondaryMuscles": [3, 4],
                "equipment": None,
                "force": "push",
                "mechanic": "compound",
                "instructions": "Be strong.",
            },
        ),
    ],
)
async def test_create_user_exercise_success(
    app: "FastAPI",
    user_client: "AsyncClient",
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
    assert response_data["name"] == payload["name"]
    assert len(response_data["primaryMuscles"]) == 1
    assert response_data["difficultyLevel"] == "beginner"
    assert response_data["category"] == "strength"

    if payload_type == "full":
        assert len(response_data["secondaryMuscles"]) == 2  # noqa: PLR2004
        assert response_data["equipment"] == []
        assert response_data["force"] == "push"
        assert response_data["mechanic"] == "compound"
        assert response_data["instructions"] == "Be strong."
    else:
        assert response_data["secondaryMuscles"] == []
        assert response_data["equipment"] == []
        assert response_data["force"] is None
        assert response_data["mechanic"] is None
        assert response_data["instructions"] is None


async def test_create_user_exercise_validation_errors(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    invalid_payload = {
        "name": "No",
        "primaryMuscles": [],
        "secondaryMuscles": [],
        "equipment": [],
        "difficultyLevel": "invalid",
        "category": "invalid",
    }

    response = await user_client.post(
        app.url_path_for("exercises:create"),
        json=invalid_payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert "name" in error_fields
    assert "primaryMuscles" in error_fields
    assert "difficultyLevel" in error_fields
    assert "category" in error_fields
    assert "secondaryMuscles" in error_fields
    assert "equipment" in error_fields


async def test_create_user_exercise_409(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    payload = {
        "name": c.USER_EXEMPLE_EXERCISE_NAME,
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
    }

    response = await user_client.post(
        app.url_path_for("exercises:create"),
        json=payload,
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    ("data", "error_msg"),
    [
        ({"pr_m": [99], "sec_m": [99], "eq": [1], "tags": [1]}, "Primary [99] and secondary [99]"),
        ({"pr_m": [99], "sec_m": [1], "eq": [1], "tags": [1]}, "Primary"),
        ({"pr_m": [1], "sec_m": [99], "eq": [1], "tags": [1]}, "Secondary"),
        ({"pr_m": [1], "sec_m": [1], "eq": [99], "tags": [1]}, "Equipment"),
        ({"pr_m": [1], "sec_m": [1], "eq": [1], "tags": [99]}, "Tags"),
    ],
)
async def test_catalog_items_not_found(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    data: dict[str, list[int]],
    error_msg: str,
) -> None:
    """Verify 404 error when muscle, equipment, or tag IDs are missing."""
    payload = {
        "name": "Test Exercise",
        "primaryMuscles": data["pr_m"],
        "secondaryMuscles": data["sec_m"],
        "equipment": data["eq"],
        "tags": data["tags"],
        "difficultyLevel": "beginner",
        "category": "strength",
        "instructions": "Be strong.",
    }
    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )
    resp_error = response.json()["detail"]
    assert error_msg in resp_error


async def test_create_system_exercise_success(
    app: "FastAPI",
    superuser_client: "AsyncClient",
) -> None:
    """Confirm superuser can create a system exercise and find it via slug.

    Scenario:
    1. POST a new system exercise with full metadata (muscles, tags, images).
    2. Slugify the name and perform a GET search by the generated slug.
    3. Verify that the retrieved exercise matches the original payload.
    """
    name = "Elite Bench Press"
    payload = {
        "name": name,
        "primaryMuscles": [1, 3, 5],
        "secondaryMuscles": None,
        "equipment": None,
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": "Professional form only.",
        "tags": [1],
        "imagePathStart": "/elite-bench-press/start.jpg",
        "imagePathEnd": "/elite-bench-press/end.jpg",
    }
    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED

    expected_slug = slugify(name)
    find_res = await superuser_client.get(
        app.url_path_for("exercises:find"),
        params={"slug": expected_slug},
    )
    assert find_res.status_code == status.HTTP_200_OK
    assert find_res.json()["name"] == name


async def test_create_system_exercise_validation_errors(
    app: "FastAPI",
    superuser_client: "AsyncClient",
) -> None:
    payload = {
        "name": None,
        "primaryMuscles": [1],
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": None,
        "tags": [],
    }

    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert "name" in error_fields
    assert "instructions" in error_fields
    assert "tags" in error_fields


@pytest.mark.parametrize("name", ["Adductor/Groin", "Adductor Groin", "Adductor-Groin"])
async def test_create_system_exercise_409(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    name: str,
) -> None:
    payload = {
        "name": name,
        "primaryMuscles": [1],
        "difficultyLevel": "beginner",
        "category": "strength",
        "instructions": "Be strong.",
        "tags": [1],
    }

    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    ("image_path", "status_code"),
    [
        ("/bench-press/1.jpg", status.HTTP_201_CREATED),
        ("/underscore_v1/dash-v2.jpeg", status.HTTP_201_CREATED),
        ("no-leading-slash.jpg", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("/wrong-extension.gif", status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_start_end_paths_by_create_system_exercise(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    image_path: str,
    status_code: int,
) -> None:
    """Verify image path validation rules for system exercises."""
    payload = {
        "name": "Elite Bench Press",
        "primaryMuscles": [1],
        "difficultyLevel": "expert",
        "category": "strength",
        "instructions": "Professional form only.",
        "tags": [1],
        "imagePathStart": image_path,
        "imagePathEnd": image_path,
    }
    response = await superuser_client.post(
        app.url_path_for("exercises:create-system"),
        json=payload,
    )

    assert response.status_code == status_code
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_detail = {f["field"] for f in response.json()["details"]}
        assert "imagePathStart" in error_detail
        assert "imagePathEnd" in error_detail


# --- GET and FILTERING TESTS ---


@pytest.mark.parametrize(
    ("exercise_id", "status_code"),
    [
        (c.USER_EXEMPLE_EXERCISE_ID, 200),
        (c.SYSTEM_EXERCISE_ID, 200),
        ("019d1c19-0d28-7e62-a4ab-052011e5f48c", 404),
        (c.ANOTHER_USER_EXERCISE_ID, 403),
    ],
)
async def test_get_exercise(
    app: "FastAPI",
    user_client: "AsyncClient",
    exercise_id: "UUID",
    status_code: int,
) -> None:
    """Verify access rules for system, own, and forbidden exercises."""
    response = await user_client.get(
        app.url_path_for("exercises:get", exercise_id=exercise_id),
    )
    assert response.status_code == status_code


async def test_fitness_trainer_can_read_user_exercise(
    app: "FastAPI",
    fitness_trainer_client: "AsyncClient",
) -> None:
    response = await fitness_trainer_client.get(
        app.url_path_for("exercises:get", exercise_id=c.USER_EXEMPLE_EXERCISE_ID),
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ("slug_or_name", "status_code"),
    [
        ({"name": c.USER_EXEMPLE_EXERCISE_NAME}, status.HTTP_200_OK),
        ({"name": c.ANOTHER_USER_EXERCISE_NAME}, status.HTTP_404_NOT_FOUND),
        ({"slug": "trail-running-walking"}, status.HTTP_200_OK),
        ({"slug": "trail-running-walking", "name": c.USER_EXEMPLE_EXERCISE_NAME}, status.HTTP_400_BAD_REQUEST),
        ({"name": c.USER_EXEMPLE_EXERCISE_NAME, "slug": None}, status.HTTP_200_OK),
    ],
)
async def test_find_exercise(
    app: "FastAPI",
    user_client: "AsyncClient",
    slug_or_name: dict[str, str],
    status_code: int,
) -> None:
    """Test exercise lookup by name for users and by slug for system."""
    response = await user_client.get(
        app.url_path_for("exercises:find"),
        params=slug_or_name,
    )
    assert response.status_code == status_code
    response_data = response.json()
    if status_code == status.HTTP_200_OK:
        if slug_or_name.get("name"):
            assert response_data["name"] == slug_or_name["name"]
        else:
            assert response_data["name"] == c.SYSTEM_EXERCISE_NAME


# Filtering


@pytest.mark.parametrize(
    ("scope", "total"),
    [("all", 14), ("user", 2), ("system", 12)],
)
async def test_list_exercises_base(
    app: "FastAPI",
    user_client: "AsyncClient",
    scope: str,
    total: int,
) -> None:
    """Verify list filtering by system, user, and combined scopes."""
    response = await user_client.get(
        app.url_path_for("exercises:list"),
        params={"scope": scope},
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) == total


@pytest.mark.parametrize(
    ("query_params", "expected_count"),
    [
        ({"scope": "system", "searchString": " Upright Row "}, 1),
        ({"scope": "user", "searchString": "Exercise Two"}, 1),
        ({"scope": "all", "category": "strength"}, 9),
        ({"scope": "all", "difficulty_level": "expert"}, 0),
        ({"scope": "system", "difficulty_level": "beginner"}, 6),
    ],
)
async def test_exercise_list_filters(
    app: "FastAPI",
    user_client: "AsyncClient",
    query_params: dict[str, str],
    expected_count: int,
) -> None:
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
        ({"primary_muscles": [1, 2], "scope": "user"}, 1),
        ({"primary_muscles": [1, 2], "scope": "all"}, 7),
        ({"primary_muscles": [1, 2], "scope": "system"}, 6),
        ([("primary_muscles", 99), ("primary_muscles", 99), ("scope", "all")], 0),
        ({"tags": [1, 2], "scope": "system"}, 11),
        ({"tags": [1, 2], "scope": "user"}, 0),
    ],
)
async def test_exercise_list_m2m_filters(
    app: "FastAPI",
    user_client: "AsyncClient",
    query_params: dict[str, Any],
    expected_count: int,
) -> None:
    """Test complex M2M filtering logic across all exercise scopes."""
    response = await user_client.get(
        app.url_path_for("exercises:list"),
        params=query_params,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["total"] == expected_count


# --- UPDATE TESTS (PATCH) ---


async def test_update_user_exercise_success(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    """Verify partial updates to user exercises and data persistence."""
    payload = {
        "name": "Updated User Exercise",
        "difficultyLevel": "intermediate",
        "instructions": None,
        "primaryMuscles": [4, 8],
    }
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=c.USER_EXEMPLE_EXERCISE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["name"] == payload["name"]
    assert response_data["difficultyLevel"] == payload["difficultyLevel"]
    assert response_data["instructions"] is None
    assert {m["id"] for m in response_data["primaryMuscles"]} == {4, 8}
    assert {m["id"] for m in response_data["secondaryMuscles"]} == {2, 3}
    assert {m["id"] for m in response_data["equipment"]} == {2}
    assert response_data["createdBy"] == str(c.USER_EXAMPLE_ID)


@pytest.mark.parametrize(
    ("exercise_id", "data", "status_code"),
    [
        (c.ANOTHER_USER_EXERCISE_ID, {}, status.HTTP_404_NOT_FOUND),
        (c.USER_EXEMPLE_EXERCISE_ID, {"name": c.USER_EXEMPLE_EXERCISE_NAME_TWO}, status.HTTP_409_CONFLICT),
        (c.USER_EXEMPLE_EXERCISE_ID, {"primaryMuscles": None}, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (c.USER_EXEMPLE_EXERCISE_ID, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_update_user_exercise_failed(
    app: "FastAPI",
    user_client: "AsyncClient",
    exercise_id: "UUID",
    data: dict[str, str],
    status_code: int,
) -> None:
    response = await user_client.patch(
        app.url_path_for("exercises:update", exercise_id=exercise_id),
        json=data,
    )
    assert response.status_code == status_code


async def test_update_system_exercise_success(
    app: "FastAPI",
    superuser_client: "AsyncClient",
) -> None:
    payload = {
        "name": "Elite Bench Press",
        "secondaryMuscles": [1, 2, 3],
        "equipment": [1, 2, 3],
        "tags": [1, 3, 4],
        "imagePathStart": None,
        "imagePathEnd": None,
    }
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == c.SYSTEM_EXERCISE_ID
    assert {m["id"] for m in response_data["primaryMuscles"]} == {4}
    assert {m["id"] for m in response_data["secondaryMuscles"]} == {1, 2, 3}
    assert {m["id"] for m in response_data["equipment"]} == {1, 2, 3}
    assert {m["id"] for m in response_data["tags"]} == {1, 3, 4}
    assert response_data["imagePathStart"] is None
    assert response_data["imagePathEnd"] is None
    assert response_data["name"] == payload["name"]


@pytest.mark.parametrize(
    ("data", "verify_slug"),
    [
        ({}, False),
        ({"name": "Elite Bench Press"}, True),
    ],
)
async def test_update_system_exercise_slug_updates(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    data: dict[str, str],
    verify_slug: bool,
) -> None:
    """Verify that updating exercise name synchronizes its unique slug.

    Scenario:
    1. Update the 'name' field via PATCH.
    2. Confirm the 'slug' in the response matches the new name.
    3. Perform a GET by slug to ensure the exercise is retrievable.
    """
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    slug = "trail-running-walking"
    if data.get("name", ""):
        slug = slugify(data["name"])
    assert response_data["slug"] == slug
    if verify_slug:
        response_verify = await superuser_client.get(
            app.url_path_for("exercises:find"),
            params={"slug": slug},
        )
        assert response_verify.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ("exercise_id", "data", "status_code"),
    [
        (c.SYSTEM_EXERCISE_ID, {"name": None}, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (c.SYSTEM_EXERCISE_ID, {"name": c.SYSTEM_EXERCISE_NAME_TWO.replace("-", "/")}, status.HTTP_409_CONFLICT),
        (c.SYSTEM_EXERCISE_ID, {"primaryMuscles": []}, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (c.SYSTEM_EXERCISE_ID, {"tags": []}, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("019d1c19-0d25-7633-8fc0-bbfa290e5088", {}, status.HTTP_404_NOT_FOUND),
    ],
)
async def test_update_system_exercise_failed(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    exercise_id: "UUID",
    data: dict[str, Any],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=exercise_id),
        json=data,
    )
    assert response.status_code == status_code


@pytest.mark.parametrize(
    ("image_path", "status_code"),
    [
        ("/bench-press/1.jpg", status.HTTP_200_OK),
        ("/underscore_v1/dash-v2.jpeg", status.HTTP_200_OK),
        ("no-leading-slash.jpg", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("/wrong-extension.gif", status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_start_end_paths_by_update_system_exercise(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    image_path: str,
    status_code: int,
) -> None:
    """Verify image path validation during system exercise updates."""
    payload = {
        "imagePathStart": image_path,
        "imagePathEnd": image_path,
    }
    response = await superuser_client.patch(
        app.url_path_for("exercises:update-system", exercise_id=c.SYSTEM_EXERCISE_ID),
        json=payload,
    )

    assert response.status_code == status_code
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_detail = {f["field"] for f in response.json()["details"]}
        assert "imagePathStart" in error_detail
        assert "imagePathEnd" in error_detail


# --- DELETE TESTS ---


@pytest.mark.parametrize(
    ("exercise_id", "status_code"),
    [
        (c.SYSTEM_EXERCISE_ID, status.HTTP_403_FORBIDDEN),
        (c.ANOTHER_USER_EXERCISE_ID, status.HTTP_403_FORBIDDEN),
        (c.USER_EXEMPLE_EXERCISE_ID, status.HTTP_204_NO_CONTENT),
        ("019d1c19-0d26-7330-b1af-91601739d0cd", status.HTTP_404_NOT_FOUND),
    ],
)
async def test_delete_user_exercise(
    app: "FastAPI",
    user_client: "AsyncClient",
    exercise_id: "UUID",
    status_code: int,
) -> None:
    """Verify that users can delete only their own exercises.

    Scenario:
    1. Attempt to delete system and other users' exercises (expect 403).
    2. Delete the user's own exercise (expect 204).
    3. Attempt to GET the deleted exercise to confirm 404.
    """
    response = await user_client.delete(app.url_path_for("exercises:delete", exercise_id=exercise_id))
    assert response.status_code == status_code
    if status_code == status.HTTP_204_NO_CONTENT:
        response = await user_client.get(app.url_path_for("exercises:get", exercise_id=exercise_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_exercise_by_superuser(
    app: "FastAPI",
    superuser_client: "AsyncClient",
) -> None:
    response = await superuser_client.delete(
        app.url_path_for("exercises:delete", exercise_id=c.SYSTEM_EXERCISE_ID),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_fitness_trainer_cannot_delete_user_exercise(
    app: "FastAPI",
    fitness_trainer_client: "AsyncClient",
) -> None:
    response = await fitness_trainer_client.delete(
        app.url_path_for("exercises:delete", exercise_id=c.USER_EXEMPLE_EXERCISE_ID)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- ACCESS TESTS ---


@pytest.mark.parametrize(
    ("url_path", "exercise_id", "method"),
    [
        ("exercises:create-system", None, "post"),
        ("exercises:update-system", c.SYSTEM_EXERCISE_ID, "patch"),
    ],
)
async def test_regular_user_access_forbidden(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_path: str,
    exercise_id: "UUID | None",
    method: str,
) -> None:
    """Ensure administrative endpoints are restricted to regular users."""
    path_params = {"exercise_id": exercise_id} if exercise_id is not None else {}
    url = app.url_path_for(url_path, **path_params)
    http_method = getattr(user_client, method)

    response = await http_method(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
