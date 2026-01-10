from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest
from fastapi import status

from app.domain.users.jwt_helpers import (
    add_token_to_blacklist,
    is_token_in_blacklist,
)
from app.lib.jwt_utils import decode_jwt
from tests import constants
from tests.helpers import wait_for_blacklist_entry

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from pytest_mock import MockerFixture
    from redis.asyncio import Redis


pytestmark = pytest.mark.anyio

# --- Basic & Integration Tests ---


@pytest.mark.parametrize(
    ("username", "password", "expected_status_code"),
    [
        (constants.SUPERUSER_EMAIL, "Test_Password1!", status.HTTP_204_NO_CONTENT),
        ("superuser123@example.com", "Test_Password1!", status.HTTP_401_UNAUTHORIZED),
        (constants.USER_EXAMPLE_EMAIL, "Test_Password2!", status.HTTP_204_NO_CONTENT),
        (constants.USER_EXAMPLE_EMAIL, "Test_Password123!", status.HTTP_401_UNAUTHORIZED),
        (constants.INACTIVE_USER_EMAIL, "Old_Password2!", status.HTTP_401_UNAUTHORIZED),
        (constants.INACTIVE_USER_EMAIL, "Old_Password123!", status.HTTP_401_UNAUTHORIZED),
    ],
)
async def test_user_login(
    client: "AsyncClient",
    app: "FastAPI",
    username: str,
    password: str,
    expected_status_code: int,
) -> None:
    """Test login with various credentials."""
    response = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": username, "password": password},
    )
    assert response.status_code == expected_status_code


async def test_user_login_tokens_exist(
    client: "AsyncClient",
    app: "FastAPI",
) -> None:
    response = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": constants.USER_EXAMPLE_EMAIL, "password": "Test_Password2!"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    cookies = dict(response.cookies)
    assert cookies.get("access_token") is not None
    assert cookies.get("refresh_token") is not None


@pytest.mark.parametrize(
    ("register_data", "status_code"),
    [
        pytest.param(
            {
                "email": "new.user@example.com",
                "password": "Test_pwd123",
                "confirm_password": "Test_pwd123",
            },
            status.HTTP_201_CREATED,
            id="success_register_without_name",
        ),
        pytest.param(
            {
                "name": "User Example",
                "email": constants.USER_EXAMPLE_EMAIL,
                "password": "Test_Password12@",
                "confirm_password": "Test_Password12@",
            },
            status.HTTP_409_CONFLICT,
            id="error_email_exists",
        ),
        pytest.param(
            {
                "name": "User  First",
                "email": "user.first@example.com",
                "password": "SecretT1@",
                "confirm_password": "SecretT1@",
            },
            status.HTTP_201_CREATED,
            id="success_register_with_name",
        ),
        pytest.param(
            {
                "name": "User Second",
                "email": "user.second@example.com",
                "password": "SecretT1@",
                "confirm_password": "secretT1@",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            id="error_pwd_not_match",
        ),
        pytest.param(
            {
                "email": "user.three@example.com",
                "password": "secret",
                "confirm_password": "secret",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            id="error_weak_password",
        ),
        pytest.param(
            {
                "name": "User Four",
                "email": "user.four.com",
                "password": "secretT1@",
                "confirm_password": "secretT1@",
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            id="error_incorrect_email",
        ),
    ],
)
async def test_user_signup(
    client: "AsyncClient",
    app: "FastAPI",
    register_data: dict[str, Any],
    status_code: int,
) -> None:
    """Test user registration validation rules."""
    response = await client.post(
        url=app.url_path_for("access:signup"),
        json=register_data,
    )
    assert response.status_code == status_code
    response_data = response.json()
    if status_code == status.HTTP_201_CREATED:
        assert "password" not in response_data
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        error_detail = response_data["details"][0]
        if error_detail["field"] == "body":
            msg = "Passwords don't match"
            assert msg in error_detail["message"]
        else:
            assert error_detail["field"] in ("password", "email")


async def test_user_refresh_token(
    app: "FastAPI",
    token_client: tuple["AsyncClient", dict[str, str]],
    redis_client: "Redis",
) -> None:
    """Verify successful access token rotation and old token blacklisting."""
    client, original_tokens_data = token_client
    original_access_token = original_tokens_data["original_access_token"]
    original_refresh_token = original_tokens_data["original_refresh_token"]
    response = await client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    cookies = dict(response.cookies)
    new_access_token = cookies["access_token"]
    new_refresh_token = cookies["refresh_token"]
    assert new_access_token is not None
    assert new_refresh_token is not None
    assert new_access_token != original_access_token
    assert new_refresh_token != original_refresh_token
    refresh_token_payload = decode_jwt(token=original_refresh_token)
    refresh_jti = refresh_token_payload["jti"]
    await wait_for_blacklist_entry(
        redis_client=redis_client,
        key=f"revoked:{refresh_jti}",
    )
    assert await is_token_in_blacklist(refresh_token_identifier=refresh_jti, redis_client=redis_client)


async def test_user_refresh_token_expired(
    app: "FastAPI",
    token_client_expired: "AsyncClient",
) -> None:
    """Ensure expired refresh tokens are rejected."""
    response = await token_client_expired.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_user_refresh_token_blacklisted(
    app: "FastAPI",
    token_client: tuple["AsyncClient", dict[str, str]],
    redis_client: "Redis",
) -> None:
    client, original_tokens_data = token_client
    refresh_token = original_tokens_data["original_refresh_token"]
    refresh_token_payload = decode_jwt(token=refresh_token)
    refresh_jti = refresh_token_payload["jti"]
    await add_token_to_blacklist(
        refresh_token_identifier=refresh_jti,
        redis_client=redis_client,
    )
    response = await client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_user_logout(
    app: "FastAPI",
    token_client: tuple["AsyncClient", dict[str, str]],
    redis_client: "Redis",
    mocker: "MockerFixture",
) -> None:
    """Test logout side effects: cookie removal and cache invalidation."""
    client, tokens_data = token_client
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.utils.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await client.post(url=app.url_path_for("access:logout"))
    cookies = dict(response.cookies)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not cookies
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
        redis_client=redis_client,
    )
    refresh_token = tokens_data["original_refresh_token"]
    refresh_token_payload = decode_jwt(refresh_token)
    refresh_jti = refresh_token_payload["jti"]
    await wait_for_blacklist_entry(
        redis_client=redis_client,
        key=f"revoked:{refresh_jti}",
    )
    assert await is_token_in_blacklist(refresh_token_identifier=refresh_jti, redis_client=redis_client)


@pytest.mark.parametrize(
    ("current_pwd", "new_pwd", "expected_status_code"),
    [
        ("Test_Password2!", "New_Password@1", status.HTTP_204_NO_CONTENT),
        ("Test_Password3!", "New_Password@2", status.HTTP_401_UNAUTHORIZED),
    ],
)
async def test_user_update_pwd(
    app: "FastAPI",
    user_client: "AsyncClient",
    current_pwd: str,
    new_pwd: str,
    expected_status_code: int,
    mocker: "MockerFixture",
) -> None:
    _ = mocker.patch(
        "app.domain.users.controllers.access.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await user_client.patch(
        url=app.url_path_for("access:update-pwd"),
        json={"current_password": current_pwd, "new_password": new_pwd},
    )
    assert response.status_code == expected_status_code


async def test_user_get_self_info(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    response = await user_client.get(url=app.url_path_for("access:profile"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(constants.USER_EXAMPLE_ID)
    assert response_data["email"] == constants.USER_EXAMPLE_EMAIL
    assert response_data["role_slug"] == "application-access"
    assert "password" not in response_data


@pytest.mark.parametrize(
    ("path_name", "method"),
    [
        ("access:refresh", "post"),
        ("access:logout", "post"),
        ("access:update-pwd", "patch"),
        ("access:profile", "get"),
    ],
)
async def test_unauthorized_user(
    client: "AsyncClient",
    app: "FastAPI",
    path_name: str,
    method: str,
) -> None:
    """Verify that protected endpoints return 401 for unauthenticated requests."""
    url = app.url_path_for(path_name)
    http_method = getattr(client, method)
    if method not in ("get",):
        response = await http_method(url, json={})
    else:
        response = await http_method(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Scenario Tests (Multi-step Flows) ---


async def test_user_logout_invalidates_current_session(
    app: "FastAPI",
    client: "AsyncClient",
) -> None:
    """Verifies that the user session is fully terminated after logout.

    Scenario: Confirm that once the logout endpoint is called, the session
    cookies are invalidated, and subsequent attempts to access protected
    endpoints (like profile) return a 401 Unauthorized status.
    """
    res_login = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": constants.USER_EXAMPLE_EMAIL, "password": "Test_Password2!"},
    )
    assert res_login.status_code == status.HTTP_204_NO_CONTENT
    res_logout = await client.post(url=app.url_path_for("access:logout"))
    assert res_logout.status_code == status.HTTP_204_NO_CONTENT
    res_self_info_unauthorized = await client.get(url=app.url_path_for("access:profile"))
    assert res_self_info_unauthorized.status_code == status.HTTP_401_UNAUTHORIZED


async def test_pwd_update_invalidates_current_session(
    app: "FastAPI",
    client: "AsyncClient",
) -> None:
    """Verifies that a password update forces a session logout.

    Scenario: Ensure that changing the password clears all authentication
    cookies and invalidates the server-side session to prevent unauthorized access.
    """
    res_login = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": constants.USER_EXAMPLE_EMAIL, "password": "Test_Password2!"},
    )
    assert res_login.status_code == status.HTTP_204_NO_CONTENT
    update_res = await client.patch(
        url=app.url_path_for("access:update-pwd"),
        json={"current_password": "Test_Password2!", "new_password": "New_Password2!"},
    )
    assert update_res.status_code == status.HTTP_204_NO_CONTENT
    cookies = dict(update_res.cookies)
    assert not cookies
    response_self_info = await client.get(url=app.url_path_for("access:profile"))
    assert response_self_info.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_after_update_pwd(
    app: "FastAPI",
    user_client: "AsyncClient",
    mocker: "MockerFixture",
    redis_client: "Redis",
) -> None:
    """Verifies user authentication flow after a password update.

    Scenario: Ensure that the user can successfully log in using their new
    credentials after the old session has been invalidated.
    """
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.controllers.access.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await user_client.patch(
        url=app.url_path_for("access:update-pwd"),
        json={"current_password": "Test_Password2!", "new_password": "New_Password@2"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
        redis_client=redis_client,
    )
    response = await user_client.post(
        url=app.url_path_for("access:login"),
        data={"username": constants.USER_EXAMPLE_EMAIL, "password": "New_Password@2"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
