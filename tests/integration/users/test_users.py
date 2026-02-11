from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi import status

from tests import constants

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from pytest_mock import MockerFixture

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("create_data", "status_code"),
    [
        pytest.param(
            {
                "name": "Test User1",
                "email": "test.user@example.com",
                "password": "Test_Password1",
                "isSuperuser": False,
            },
            status.HTTP_201_CREATED,
            id="success_create_regular_user",
        ),
        pytest.param(
            {
                "name": "Test User2",
                "email": constants.USER_EXAMPLE_EMAIL,
                "password": "Test_Password2",
            },
            status.HTTP_409_CONFLICT,
            id="error_duplicate_email",
        ),
        pytest.param(
            {
                "name": "Admin User",
                "email": "admin@example.com",
                "password": "Test_Password3",
                "isSuperuser": True,
            },
            status.HTTP_201_CREATED,
            id="success_create_admin",
        ),
        pytest.param(
            {
                "name": "Test User3",
                "email": "user@example.com",
                "password": "Te",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="error_password_too_short",
        ),
        pytest.param(
            {
                "name": "Test User4",
                "email": "bad.com",
                "password": "Test_Password4",
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="error_invalid_email",
        ),
    ],
)
async def test_create_user(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    create_data: dict[str, str | bool],
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("users:create"),
        json=create_data,
    )
    assert response.status_code == status_code
    response_data = response.json()
    if status_code == status.HTTP_201_CREATED:
        assert "id" in response_data
        assert response_data["email"] == create_data["email"]
        assert response_data["isSuperuser"] is create_data.get("isSuperuser", False)
        assert response_data["isActive"] is True
        assert "password" not in response_data
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_detail = response_data["details"][0]
        assert error_detail["field"] in ("password", "email")


@pytest.mark.parametrize(
    ("user_id", "status_code"),
    [
        pytest.param(
            constants.USER_EXAMPLE_ID,
            status.HTTP_200_OK,
            id="success_get_user",
        ),
        pytest.param(
            UUID("019a5f0c-3a24-7693-abf4-3ed68ea9cf02"),
            status.HTTP_404_NOT_FOUND,
            id="error_user_not_found",
        ),
    ],
)
async def test_get_user(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    user_id: UUID,
    status_code: int,
) -> None:
    response = await superuser_client.get(app.url_path_for("users:get", user_id=user_id))
    assert response.status_code == status_code


async def test_get_list_users(
    superuser_client: "AsyncClient",
    app: "FastAPI",
) -> None:
    response = await superuser_client.get(app.url_path_for("users:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data["items"], list)
    assert int(response_data["total"]) > 1


@pytest.mark.parametrize(
    ("search", "total", "status_code"),
    [
        pytest.param(
            constants.ANOTHER_USER_EMAIL,
            1,
            status.HTTP_200_OK,
            id="filtered_user_exists",
        ),
        pytest.param(
            "non.existent@example.com",
            0,
            status.HTTP_200_OK,
            id="filtered_user_non_exists",
        ),
    ],
)
async def test_get_list_users_filtered(
    superuser_client: "AsyncClient",
    app: "FastAPI",
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
    superuser_client: "AsyncClient",
    app: "FastAPI",
) -> None:
    response_first = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"pageSize": 1, "currentPage": 1},
    )
    data_first = response_first.json()
    assert len(data_first["items"]) == 1
    first_user_id = data_first["items"][0]["id"]

    response_second = await superuser_client.get(
        app.url_path_for("users:list"),
        params={"pageSize": 1, "currentPage": 2},
    )
    data_second = response_second.json()
    assert len(data_second["items"]) == 1
    second_user_id = data_second["items"][0]["id"]
    assert first_user_id != second_user_id
    assert int(data_first["total"]) >= 2  # noqa: PLR2004


@pytest.mark.parametrize(
    ("user_id", "update_data", "status_code"),
    [
        pytest.param(
            constants.USER_EXAMPLE_ID,
            {
                "name": "New Name",
                "email": "new@example.com",
                "password": "Test_pwd",
            },
            status.HTTP_200_OK,
            id="success_update_fields",
        ),
        pytest.param(
            constants.ANOTHER_USER_ID,
            {
                "name": "Admin",
                "email": "admin@example.com",
                "password": "Admin_pwd",
                "isSuperuser": True,
            },
            status.HTTP_200_OK,
            id="success_update_to_admin",
        ),
        pytest.param(
            UUID("019a643e-db0a-77d0-89a6-0536f6d00a21"),
            {
                "name": "Not Exists",
                "email": "non.exists@example.com",
                "password": "Test_pwd",
            },
            status.HTTP_404_NOT_FOUND,
            id="error_user_not_found",
        ),
        pytest.param(
            constants.USER_EXAMPLE_ID,
            {
                "name": "New Name",
                "email": constants.ANOTHER_USER_EMAIL,
                "password": "Test_pwd",
            },
            status.HTTP_409_CONFLICT,
            id="error_email_exists",
        ),
        pytest.param(
            constants.USER_EXAMPLE_ID,
            {"name": "New Name", "email": "bad.example.com"},
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="error_incorrect_email",
        ),
        pytest.param(
            constants.USER_EXAMPLE_ID,
            {"name": "New Name", "password": "Te"},
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="error_to_short_pwd",
        ),
        pytest.param(
            constants.SUPERUSER_ID,
            {"isSuperuser": False},
            status.HTTP_403_FORBIDDEN,
            id="error_self_action_forbidden",
        ),
        pytest.param(
            constants.DEFAULT_ADMIN_ID,
            {"isSuperuser": False},
            status.HTTP_403_FORBIDDEN,
            id="error_action_on_system_admin_forbidden",
        ),
    ],
)
async def test_update_user(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    mocker: "MockerFixture",
    user_id: UUID,
    update_data: dict[str, str | bool],
    status_code: int,
) -> None:
    _ = mocker.patch(
        "app.domain.users.controllers.users.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=user_id),
        json=update_data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        response_data = response.json()
        error_detail = response_data["details"][0]
        assert error_detail["field"] in ("password", "email")


async def test_update_user_cache_invalidate_called(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    mocker: "MockerFixture",
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.controllers.users.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    update_data = {
        "name": "New Name",
        "email": "new.user@example.com",
        "password": "New_pwd",
    }
    response = await superuser_client.patch(
        app.url_path_for("users:update", user_id=constants.USER_EXAMPLE_ID),
        json=update_data,
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert UUID(response_data["id"]) == constants.USER_EXAMPLE_ID
    assert response_data["email"] == update_data["email"]
    assert "password" not in response_data
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )


@pytest.mark.parametrize(
    ("user_id", "status_code"),
    [
        (constants.USER_EXAMPLE_ID, status.HTTP_204_NO_CONTENT),
        (UUID("019a5f0c-3a24-7693-abf4-3ed68ea9cf03"), status.HTTP_404_NOT_FOUND),
        (constants.SUPERUSER_ID, status.HTTP_403_FORBIDDEN),
        (constants.DEFAULT_ADMIN_ID, status.HTTP_403_FORBIDDEN),
    ],
)
async def test_delete_user(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    user_id: UUID,
    status_code: int,
) -> None:
    response = await superuser_client.delete(app.url_path_for("users:delete", user_id=user_id))
    assert response.status_code == status_code


async def test_delete_user_cache_invalidated(
    superuser_client: "AsyncClient",
    app: "FastAPI",
    mocker: "MockerFixture",
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.controllers.users.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    _ = await superuser_client.delete(
        app.url_path_for("users:delete", user_id=constants.USER_EXAMPLE_ID),
    )
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )


@pytest.mark.parametrize(
    ("url_path", "user_id", "method"),
    [
        ("users:create", None, "post"),
        ("users:get", constants.ANOTHER_USER_ID, "get"),
        ("users:list", None, "get"),
        ("users:update", constants.ANOTHER_USER_ID, "patch"),
        ("users:delete", constants.ANOTHER_USER_ID, "delete"),
    ],
)
async def test_regular_user_access_forbidden(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_path: str,
    user_id: UUID | None,
    method: str,
) -> None:
    url = app.url_path_for(url_path, user_id=user_id) if user_id is not None else app.url_path_for(url_path)
    http_method = getattr(user_client, method)
    if method in ("get", "delete"):
        response = await http_method(url)
    else:
        response = await http_method(url, json={})
    assert response.status_code == status.HTTP_403_FORBIDDEN
