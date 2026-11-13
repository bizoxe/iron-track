from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
from fastapi import status

from tests import constants

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from pytest_mock import MockerFixture

pytestmark = pytest.mark.anyio


# --- Create ---


@pytest.mark.parametrize(
    ("payload", "error_field", "status_code"),
    [
        pytest.param(
            {
                "name": "Test User One",
                "email": "test.one@example.com",
                "password": "A" * 125 + "1a!",
            },
            None,
            status.HTTP_201_CREATED,
            id="create_user_success",
        ),
        pytest.param(
            {
                "name": "Test User Two",
                "email": "USER@TwO.com",
                "password": "Test_Password2&",
            },
            None,
            status.HTTP_201_CREATED,
            id="email_normalized_on_save",
        ),
        pytest.param(
            {
                "name": None,
                "email": constants.USER_EXAMPLE_EMAIL.upper(),
                "password": "TestPassword!3",
            },
            None,
            status.HTTP_409_CONFLICT,
            id="duplicate_email_case_insensitive",
        ),
        pytest.param(
            {
                "name": "Test User Four",
                "email": "bad.com",
                "password": "TestPassword4@",
            },
            "email",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="invalid_email",
        ),
        pytest.param(
            {
                "name": "Test User Five",
                "email": "test.five@example.com",
                "password": "Test",
            },
            "password",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="weak_password",
        ),
        pytest.param(
            {
                "name": "Test User Six",
                "email": "test.six@example.com",
                "password": "A" * 126 + "1a!",
            },
            "password",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="password_too_long",
        ),
    ],
)
async def test_create_user(
    app: FastAPI,
    superuser_client: AsyncClient,
    payload: dict[str, Any],
    error_field: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("users:create"),
        json=payload,
    )
    assert response.status_code == status_code
    response_data = response.json()
    if status_code == status.HTTP_201_CREATED:
        assert "id" in response_data
        assert response_data["email"] == payload["email"].lower()
        assert "password" not in response_data
        assert response_data["isActive"] is True
        assert response_data["roleSlug"] == "application-access"
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_field_resp = response_data["details"][0]["field"]
        assert error_field_resp == error_field


async def test_create_user_rejects_null_required_fields(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    payload = {"email": None, "password": None}
    response = await superuser_client.post(
        app.url_path_for("users:create"),
        json=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"email", "password"}


# --- List Users ---


async def test_get_list_users(
    app: FastAPI,
    superuser_client: AsyncClient,
    raw_users: list[dict[str, Any]],
) -> None:
    response = await superuser_client.get(app.url_path_for("users:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert int(response_data["total"]) == len(raw_users)
    assert str(constants.RETIRED_USER_ID) in {item["id"] for item in response_data["items"]}


@pytest.mark.parametrize(
    ("search", "total", "status_code"),
    [
        pytest.param(
            constants.ANOTHER_USER_EMAIL,
            1,
            status.HTTP_200_OK,
            id="user_found_by_email",
        ),
        pytest.param(
            constants.USER_EXAMPLE_NAME,
            1,
            status.HTTP_200_OK,
            id="user_found_by_name",
        ),
    ],
)
async def test_get_list_users_search(
    app: FastAPI,
    superuser_client: AsyncClient,
    search: str,
    total: int,
    status_code: int,
) -> None:
    response = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"searchString": search},
    )
    assert response.status_code == status_code
    response_data = response.json()
    assert int(response_data["total"]) == total


async def test_get_list_users_pagination(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response_first = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"pageSize": 1, "currentPage": 1},
    )
    assert response_first.status_code == status.HTTP_200_OK
    data_first = response_first.json()
    assert len(data_first["items"]) == 1
    first_user_id = data_first["items"][0]["id"]

    response_second = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"pageSize": 1, "currentPage": 2},
    )
    assert response_second.status_code == status.HTTP_200_OK
    data_second = response_second.json()
    assert len(data_second["items"]) == 1
    second_user_id = data_second["items"][0]["id"]
    assert first_user_id != second_user_id


@pytest.mark.parametrize(
    ("params", "expected_email"),
    [
        pytest.param({"showOnlyBanned": True}, constants.INACTIVE_USER_EMAIL, id="banned"),
        pytest.param({"showOnlyRetired": True}, constants.RETIRED_USER_EMAIL, id="retired"),
    ],
)
async def test_get_list_users_status_slices(
    app: FastAPI,
    superuser_client: AsyncClient,
    params: dict[str, bool],
    expected_email: str,
) -> None:
    """Status slices partition accounts: each returns its own account."""
    response = await superuser_client.get(
        app.url_path_for("users:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    assert {item["email"] for item in response.json()["items"]} == {expected_email}
    assert int(response.json()["total"]) == 1


async def test_get_list_users_status_flags_mutually_exclusive(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"showOnlyBanned": True, "showOnlyRetired": True},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    ("params", "expect_all"),
    [
        pytest.param({"createdBefore": "2100-01-01T00:00:00Z"}, True, id="before_future"),
        pytest.param({"createdAfter": "2000-01-01T00:00:00Z"}, True, id="after_past"),
        pytest.param(
            {"createdAfter": "2000-01-01T00:00:00Z", "createdBefore": "2100-01-01T00:00:00Z"},
            True,
            id="range_covers_all",
        ),
        pytest.param(
            {"createdBefore": "2000-01-01T00:00:00Z"},
            False,
            id="before_past_excludes_all",
        ),
    ],
)
async def test_get_list_users_created_range(
    app: FastAPI,
    superuser_client: AsyncClient,
    raw_users: list[dict[str, Any]],
    params: dict[str, str],
    expect_all: bool,
) -> None:
    """Range bounds apply: wide ones keep all accounts; past ones exclude all."""
    response = await superuser_client.get(
        app.url_path_for("users:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    expected_total = len(raw_users) if expect_all else 0
    assert int(response.json()["total"]) == expected_total


# --- Get by ID ---


@pytest.mark.parametrize(
    ("user_id", "status_code"),
    [
        pytest.param(
            constants.USER_EXAMPLE_ID,
            status.HTTP_200_OK,
            id="success",
        ),
        pytest.param(
            UUID("019a5f0c-3a24-7693-abf4-3ed68ea9cf02"),
            status.HTTP_404_NOT_FOUND,
            id="not_found",
        ),
    ],
)
async def test_get_user(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    status_code: int,
) -> None:
    response = await superuser_client.get(app.url_path_for("users:get", user_id=user_id))
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        assert response.json()["id"] == str(user_id)


async def test_get_user_returns_soft_deleted(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """Admins need the full picture: a retired account stays readable by id."""
    response = await superuser_client.get(
        app.url_path_for("users:get", user_id=constants.RETIRED_USER_ID),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["email"] == constants.RETIRED_USER_EMAIL
    assert response_data["isActive"] is False
    assert response_data["deletedAt"] is not None


# --- Update ---


async def test_update_user_success(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    payload = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "password": "Update?Pwd123",
    }
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert UUID(response_data["id"]) == constants.USER_EXAMPLE_ID
    assert response_data["name"] == payload["name"]
    assert response_data["email"] == payload["email"]
    assert "password" not in response_data


async def test_update_user_empty_payload_is_noop(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """An empty patch changes nothing."""
    before = await superuser_client.get(
        app.url_path_for("users:get", user_id=constants.USER_EXAMPLE_ID),
    )
    assert before.status_code == status.HTTP_200_OK

    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json={},
    )
    assert response.status_code == status.HTTP_200_OK

    after = await superuser_client.get(
        app.url_path_for("users:get", user_id=constants.USER_EXAMPLE_ID),
    )
    assert after.json() == before.json()


@pytest.mark.parametrize(
    ("user_id", "patch_payload", "status_code"),
    [
        pytest.param(
            UUID("019a643e-db0a-77d0-89a6-0536f6d00a21"),
            {
                "email": "not.found@example.com",
            },
            status.HTTP_404_NOT_FOUND,
            id="user_not_found",
        ),
        pytest.param(
            constants.USER_EXAMPLE_ID,
            {
                "email": constants.ANOTHER_USER_EMAIL,
                "password": "Update*Pwd3",
            },
            status.HTTP_409_CONFLICT,
            id="duplicate_email",
        ),
        pytest.param(
            constants.SUPERUSER_ID,
            {"isActive": False},
            status.HTTP_403_FORBIDDEN,
            id="self_action_forbidden",
        ),
        pytest.param(
            constants.DEFAULT_ADMIN_ID,
            {"isActive": False},
            status.HTTP_403_FORBIDDEN,
            id="action_on_system_admin_forbidden",
        ),
    ],
)
async def test_update_user_negative_cases(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    patch_payload: dict[str, Any],
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=user_id),
        json=patch_payload,
    )
    assert response.status_code == status_code


async def test_update_user_cache_invalidation_called(
    app: FastAPI,
    superuser_client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.controllers.users.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json={"name": "Updated Name"},
    )
    assert response.status_code == status.HTTP_200_OK
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )


async def test_update_user_invalidates_cache_end_to_end(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_client: AsyncClient,
) -> None:
    """The pre-warmed auth cache must be dropped by an update.

    The warm-up request only needs to reach the identity layer (403 from the
    role gate is fine — the UserAuth cache entry is filled before it).
    """
    warmup = await user_client.get(app.url_path_for("users:list"))
    assert warmup.status_code == status.HTTP_403_FORBIDDEN

    banned = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json={"isActive": False},
    )
    assert banned.status_code == status.HTTP_200_OK

    denied = await user_client.get(app.url_path_for("users:list"))
    assert denied.status_code == status.HTTP_401_UNAUTHORIZED


async def test_update_user_skips_cache_invalidation_on_failure(
    app: FastAPI,
    superuser_client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    """Cache invalidation sits in the success branch of the update."""
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.controllers.users.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json={"email": constants.ANOTHER_USER_EMAIL},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    mock_invalidate_cache.assert_not_called()


# --- User Exercises ---


@pytest.mark.parametrize(
    ("user_id", "expected_total"),
    [
        pytest.param(constants.USER_EXAMPLE_ID, 2, id="owner_of_two"),
        pytest.param(constants.ANOTHER_USER_ID, 1, id="owner_of_one"),
    ],
)
async def test_get_list_user_exercises_returns_user_content(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    expected_total: int,
) -> None:
    """The listing returns exactly the requested user's exercises."""
    response = await superuser_client.get(
        app.url_path_for("users:list-user-exercises", user_id=user_id),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert int(response_data["total"]) == expected_total
    assert all(UUID(item["createdBy"]) == user_id for item in response_data["items"])


async def test_get_list_user_exercises_user_not_found(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """A missing user answers 404.

    This lets an admin tell 'no such user' apart from 'no exercises'.
    """
    response = await superuser_client.get(
        app.url_path_for(
            "users:list-user-exercises",
            user_id=UUID("019a6443-2c2e-7f6b-9b0e-5a3f1b7d2c44"),
        ),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_list_user_exercises_search(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.get(
        app.url_path_for("users:list-user-exercises", user_id=constants.USER_EXAMPLE_ID),
        params={"searchString": constants.USER_EXAMPLE_EXERCISE_NAME_TWO},
    )
    assert response.status_code == status.HTTP_200_OK
    assert int(response.json()["total"]) == 1


async def test_get_list_user_exercises_created_range(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    """CreatedAtRangeFilters is wired into the user-exercise listing."""
    response = await superuser_client.get(
        app.url_path_for("users:list-user-exercises", user_id=constants.USER_EXAMPLE_ID),
        params={"createdBefore": "2000-01-01T00:00:00Z"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert int(response.json()["total"]) == 0


async def test_get_user_exercise_returns_user_exercise(
    app: FastAPI,
    superuser_client: AsyncClient,
) -> None:
    response = await superuser_client.get(
        app.url_path_for(
            "users:get-user-exercise",
            user_id=constants.USER_EXAMPLE_ID,
            exercise_id=constants.USER_EXAMPLE_EXERCISE_ID,
        ),
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert UUID(response_data["id"]) == constants.USER_EXAMPLE_EXERCISE_ID
    assert UUID(response_data["createdBy"]) == constants.USER_EXAMPLE_ID


@pytest.mark.parametrize(
    ("user_id", "exercise_id"),
    [
        pytest.param(
            constants.ANOTHER_USER_ID,
            constants.USER_EXAMPLE_EXERCISE_ID,
            id="foreign_exercise",
        ),
        pytest.param(
            constants.USER_EXAMPLE_ID,
            UUID("019d1c19-0d31-7c9d-9a10-5c2f1e7b8a90"),
            id="unknown_exercise",
        ),
    ],
)
async def test_get_user_exercise_not_found(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    exercise_id: UUID,
) -> None:
    """An exercise not authored by the user does not exist for this route.

    The rejection is a uniform 404, not a 403.
    """
    response = await superuser_client.get(
        app.url_path_for(
            "users:get-user-exercise",
            user_id=user_id,
            exercise_id=exercise_id,
        ),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Access Control ---


ADMIN_ROUTES = [
    ("users:create", "post", {}),
    ("users:list", "get", {}),
    ("users:get", "get", {"user_id": constants.ANOTHER_USER_ID}),
    ("users:update", "patch", {"user_id": constants.ANOTHER_USER_ID}),
    ("users:list-user-exercises", "get", {"user_id": constants.ANOTHER_USER_ID}),
    (
        "users:get-user-exercise",
        "get",
        {"user_id": constants.ANOTHER_USER_ID, "exercise_id": constants.USER_EXAMPLE_EXERCISE_ID},
    ),
]


async def test_admin_routes_require_superuser(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    for url_path, method, path_params in ADMIN_ROUTES:
        response = await getattr(user_client, method)(app.url_path_for(url_path, **path_params))
        assert response.status_code == status.HTTP_403_FORBIDDEN, f"{url_path}: {response.status_code}"


async def test_admin_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    for url_path, method, path_params in ADMIN_ROUTES:
        response = await getattr(client, method)(app.url_path_for(url_path, **path_params))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"{url_path}: {response.status_code}"
