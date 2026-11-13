from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

import anyio
import pytest
from cashews import cache as cashews_cache
from fastapi import status
from sqlalchemy import select

from app.config.constants import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_USER_ROLE_SLUG,
    USER_AUTH_CACHE_KEY_PREFIX,
)
from app.db.models.user import User
from app.domain.accounts.jwt_helpers import (
    add_token_to_blacklist,
    create_access_token,
    create_refresh_token,
)
from app.lib.jwt_utils import decode_jwt, encode_jwt
from tests import constants
from tests.helpers import set_access_cookie

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from pytest_mock import MockerFixture
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.anyio

# --- Fixtures and helpers ---


class SessionTokens(NamedTuple):
    access: str
    refresh: str
    refresh_jti: str


@pytest.fixture(name="user_client_with_tokens")
def fx_user_client_with_tokens(user_client: AsyncClient) -> tuple[AsyncClient, SessionTokens]:
    access = user_client.cookies["access_token"]
    refresh = user_client.cookies["refresh_token"]
    tokens = SessionTokens(
        access=access,
        refresh=refresh,
        refresh_jti=decode_jwt(refresh).claims["jti"],
    )
    return user_client, tokens


def create_expired_access_token(user_id: UUID, email: str) -> str:
    jwt_payload = {"sub": str(user_id), "email": email}
    return encode_jwt(payload=jwt_payload, expire_minutes=-1)


def create_expired_refresh_token(user_id: UUID) -> str:
    jwt_payload = {"sub": str(user_id)}
    return encode_jwt(payload=jwt_payload, expire_timedelta=timedelta(minutes=-1))


async def wait_for_blacklist_entry(
    key: str,
    timeout: float = 1.0,  # noqa: ASYNC109
    interval: float = 0.01,
) -> bool:
    """Wait for a cache key to appear, polling until timeout.

    Background tasks run after the response is sent, so a direct cache
    read races with the task; polling closes that gap. Returns False on
    timeout — assert on the result to fail with context.
    """
    end_time = anyio.current_time() + timeout

    while anyio.current_time() < end_time:
        if await cashews_cache.get(key) is not None:
            return True
        await anyio.sleep(interval)

    return False


async def wait_for_auth_context_eviction(
    user_id: UUID,
    timeout: float = 1.0,  # noqa: ASYNC109
    interval: float = 0.01,
) -> bool:
    """Wait for a user's cached auth context to clear, polling until timeout.

    The access token outlives the account: `revoke_session` runs in a
    background task after the response is sent and drops the cached
    UserAuth, so a direct cache read races with it — polling mirrors
    `wait_for_blacklist_entry`. Once the entry is gone, the next
    authenticated request rebuilds the context from the database and is
    rejected. Returns False on timeout — assert on the result to fail
    with context.
    """
    end_time = anyio.current_time() + timeout

    while anyio.current_time() < end_time:
        if await cashews_cache.get(f"{USER_AUTH_CACHE_KEY_PREFIX}:{user_id}") is None:
            return True
        await anyio.sleep(interval)

    return False


# --- Registration and Login ---


@pytest.mark.parametrize(
    ("payload", "error_field", "status_code"),
    [
        pytest.param(
            {
                "name": None,
                "email": "user.unnamed@example.com",
                "password": "Test$pwd123",
                "confirmPassword": "Test$pwd123",
            },
            None,
            status.HTTP_201_CREATED,
            id="register_without_name",
        ),
        pytest.param(
            {
                "name": "New User One",
                "email": "user.one@example.com",
                "password": "TestPassword1*",
                "confirmPassword": "TestPassword1*",
            },
            None,
            status.HTTP_201_CREATED,
            id="register_with_name",
        ),
        pytest.param(
            {
                "name": "New User Two",
                "email": constants.USER_EXAMPLE_EMAIL.upper(),
                "password": "Test_Password12@",
                "confirmPassword": "Test_Password12@",
            },
            "email",
            status.HTTP_409_CONFLICT,
            id="duplicate_email_case_insensitive",
        ),
        pytest.param(
            {
                "email": "user.three@example.com",
                "password": "Test",
                "confirmPassword": "Test",
            },
            "password",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="weak_password",
        ),
        pytest.param(
            {
                "name": "New User Four",
                "email": "user.four@example.com",
                "password": "TestPassword4&",
                "confirmPassword": "TestPassword22&",
            },
            "body",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="password_not_match",
        ),
        pytest.param(
            {
                "name": "New User Five",
                "email": "bad.com",
                "password": "TestPassword5&",
                "confirmPassword": "TestPassword5&",
            },
            "email",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="invalid_email",
        ),
        pytest.param(
            {
                "name": "New User Six",
                "email": "USER.six@EXAMPLE.com",
                "password": "TestPassword6#",
                "confirmPassword": "TestPassword6#",
            },
            None,
            status.HTTP_201_CREATED,
            id="register_normalizes_email",
        ),
    ],
)
async def test_register(
    app: FastAPI,
    client: AsyncClient,
    payload: dict[str, Any],
    error_field: str | None,
    status_code: int,
) -> None:
    response = await client.post(
        url=app.url_path_for("access:register"),
        json=payload,
    )
    assert response.status_code == status_code
    response_data = response.json()
    if response.status_code == status.HTTP_201_CREATED:
        assert response_data["name"] == payload["name"]
        assert response_data["email"] == payload["email"].lower()
        assert response_data["roleSlug"] == DEFAULT_USER_ROLE_SLUG
        assert "password" not in response_data
    if response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_field_resp = response_data["details"][0]["field"]
        assert error_field_resp == error_field


async def test_register_rejects_null_required_fields(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Required fields reject nulls in the register payload.

    The matrix rows never send nulls; required-ness is pinned on
    AccountRegister's own declarations.
    """
    payload = {"email": None, "password": None, "confirmPassword": None}
    response = await client.post(url=app.url_path_for("access:register"), json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_fields = {f["field"] for f in response.json()["details"]}
    assert error_fields == {"email", "password", "confirmPassword"}


async def test_register_rejects_unknown_fields(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Unknown fields are rejected, not ignored (extra=forbid).

    The suite's only pin of extra=forbid; registration is the public
    surface where a permissive schema would hurt most — a client-supplied
    isSuperuser flag must fail loudly.
    """
    response = await client.post(
        url=app.url_path_for("access:register"),
        json={
            "name": "Escalation Attempt",
            "email": "escalation@example.com",
            "password": "EscalationPassword1#",
            "confirmPassword": "EscalationPassword1#",
            "isSuperuser": True,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error_type = response.json()["details"][0]["type"]
    assert error_type == "extra_forbidden"


@pytest.mark.parametrize(
    ("username", "password", "status_code"),
    [
        pytest.param(
            constants.USER_EXAMPLE_EMAIL.upper(),
            "Test_Password2!",
            status.HTTP_204_NO_CONTENT,
            id="login_case_insensitive",
        ),
        pytest.param(
            constants.USER_EXAMPLE_EMAIL, "WrongPassword123!", status.HTTP_401_UNAUTHORIZED, id="wrong_password"
        ),
        pytest.param(constants.SUPERUSER_EMAIL, "Test_Password1!", status.HTTP_204_NO_CONTENT, id="superuser_login"),
        pytest.param(
            "unauthenticated@example.com", "UnauthenticatedPassword1!", status.HTTP_401_UNAUTHORIZED, id="unknown_email"
        ),
        pytest.param(
            constants.INACTIVE_USER_EMAIL,
            "InactivePassword2!",
            status.HTTP_401_UNAUTHORIZED,
            id="inactive_correct_password",
        ),
        pytest.param(constants.RETIRED_USER_EMAIL, "Test_Password5!", status.HTTP_401_UNAUTHORIZED, id="retired_user"),
    ],
)
async def test_login(
    app: FastAPI,
    client: AsyncClient,
    username: str,
    password: str,
    status_code: int,
) -> None:
    response = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": username, "password": password},
    )
    assert response.status_code == status_code


async def test_login_tokens_exist(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    response = await client.post(
        url=app.url_path_for("access:login"),
        data={"username": constants.USER_EXAMPLE_EMAIL, "password": "Test_Password2!"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    cookies = dict(response.cookies)
    assert cookies.get("access_token") is not None
    assert cookies.get("refresh_token") is not None


# --- Profile ---


async def test_get_self_info(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    response = await user_client.get(url=app.url_path_for("access:profile"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(constants.USER_EXAMPLE_ID)
    assert response_data["email"] == constants.USER_EXAMPLE_EMAIL
    assert response_data["roleSlug"] == DEFAULT_USER_ROLE_SLUG
    assert "password" not in response_data


# --- Refresh Tokens ---


async def test_refresh_token_rotates_tokens_and_blacklists_old(
    app: FastAPI,
    user_client_with_tokens: tuple[AsyncClient, SessionTokens],
) -> None:
    """Tokens issued by a refresh call replace the pair and retire the old one.

    The old refresh token must land in the blacklist while both cookies
    change; new tokens equal to the old ones would mean the route kept
    the session as is.
    """
    client, tokens = user_client_with_tokens
    response = await client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    new_cookies = dict(response.cookies)
    assert new_cookies["access_token"] != tokens.access
    assert new_cookies["refresh_token"] != tokens.refresh
    assert await wait_for_blacklist_entry(key=f"revoked:{tokens.refresh_jti}")


async def test_refresh_token_rejects_expired_token(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    """An expired refresh token is rejected on the refresh path.

    Decode fails before the blacklist and user lookups run, so with the
    account live the 401 is attributable to exp alone.
    """
    user_client.cookies.set(
        name="refresh_token",
        value=create_expired_refresh_token(user_id=constants.USER_EXAMPLE_ID),
    )
    response = await user_client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_rejects_blacklisted(
    app: FastAPI,
    user_client_with_tokens: tuple[AsyncClient, SessionTokens],
) -> None:
    """A blacklisted refresh token is rejected on the refresh path.

    The blacklist entry is seeded by hand — this is the only test that
    enters the route with an already-revoked token, so the only one that
    exercises the blacklist check on read.
    """
    client, tokens = user_client_with_tokens
    await add_token_to_blacklist(
        refresh_token_identifier=tokens.refresh_jti,
        ttl=60,
    )
    response = await client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_rejects_access_token_in_refresh_cookie(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    """An access token in the refresh cookie is answered with 401, not 500.

    Both token types share the signing key, so the signature verifies; the
    extra access claim raises TypeError in the Struct constructor. Without
    TypeError in the except clause this path would answer 500.
    """
    user_client.cookies.set(
        name="refresh_token",
        value=create_access_token(
            user_id=constants.USER_EXAMPLE_ID,
            email=constants.USER_EXAMPLE_EMAIL,
        ),
    )
    response = await user_client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_inactive_user(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """A deactivated account cannot rotate its tokens."""
    refresh_token = create_refresh_token(user_id=constants.INACTIVE_USER_ID)
    client.cookies.set(name="refresh_token", value=refresh_token)
    response = await client.post(url=app.url_path_for("access:refresh"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Token Validation ---


async def test_access_token_survives_corrupted_cache_entry(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """A corrupted `jwt:access` cache entry falls back to full verification.

    Entries are written as raw msgpack bytes; a value that no longer decodes
    (payload schema drift between deploys) must re-verify the token instead
    of logging the user out or crashing the request.
    """
    access = set_access_cookie(
        client=client,
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    jti = decode_jwt(access).claims["jti"]
    await cashews_cache.set(key=f"jwt:access:{jti}", value=b"\xc1garbage", expire=60)
    response = await client.get(app.url_path_for("access:profile"))
    assert response.status_code == status.HTTP_200_OK


async def test_expired_access_token_rejected(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    """An expired access token is rejected while the account stays valid.

    All failure modes on this path answer with the same 401; the account
    is kept live and active so that exp remains the only possible cause.
    """
    user_client.cookies.set(
        name="access_token",
        value=create_expired_access_token(
            user_id=constants.USER_EXAMPLE_ID,
            email=constants.USER_EXAMPLE_EMAIL,
        ),
    )
    response = await user_client.get(url=app.url_path_for("access:profile"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_token_in_access_cookie_rejected(
    app: FastAPI,
    user_client: AsyncClient,
) -> None:
    """A refresh token in the access cookie is answered with 401, not 500.

    Both token types share the signing key, so the signature verifies;
    the payload shape mismatch raises TypeError in the Struct constructor.
    Without TypeError in the except clause this path would answer 500.
    """
    user_client.cookies.set(
        name="access_token",
        value=create_refresh_token(user_id=constants.USER_EXAMPLE_ID),
    )
    response = await user_client.get(url=app.url_path_for("access:profile"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Update Password ---


@pytest.mark.parametrize(
    ("payload", "error_field", "status_code"),
    [
        pytest.param(
            {"currentPassword": "Test_Password2!", "newPassword": "MyNewPassword@1"},
            None,
            status.HTTP_204_NO_CONTENT,
            id="update_password_success",
        ),
        pytest.param(
            {"currentPassword": "WrongPassword3!", "newPassword": "MyNewPassword@1"},
            None,
            status.HTTP_401_UNAUTHORIZED,
            id="wrong_password",
        ),
        pytest.param(
            {"currentPassword": "Test_Password2!", "newPassword": "weak"},
            "newPassword",
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            id="weak_password",
        ),
    ],
)
async def test_update_password(
    app: FastAPI,
    user_client: AsyncClient,
    payload: dict[str, str],
    error_field: str | None,
    status_code: int,
) -> None:
    response = await user_client.patch(
        url=app.url_path_for("access:update-password"),
        json=payload,
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        assert response.json()["details"][0]["field"] == error_field


async def test_update_password_persists_new_hash(
    app: FastAPI,
    user_client: AsyncClient,
    session: AsyncSession,
) -> None:
    """The new password hash is persisted, not just accepted.

    The hash is read back across the request; re-running argon2
    verification would only repeat production code.
    """
    old_hash = await session.scalar(
        select(User.password).where(User.id == constants.USER_EXAMPLE_ID),
    )
    response = await user_client.patch(
        url=app.url_path_for("access:update-password"),
        json={
            "currentPassword": "Test_Password2!",
            "newPassword": "NewPassword*1",
        },
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    new_hash = await session.scalar(
        select(User.password).where(User.id == constants.USER_EXAMPLE_ID),
    )
    assert new_hash != old_hash


async def test_update_password_ends_current_session(
    app: FastAPI,
    user_client_with_tokens: tuple[AsyncClient, SessionTokens],
    mocker: MockerFixture,
) -> None:
    """A single password change covers cookies, blacklist, and cache."""
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.utils.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    client, tokens = user_client_with_tokens
    response = await client.patch(
        url=app.url_path_for("access:update-password"),
        json={"currentPassword": "Test_Password2!", "newPassword": "New_Password@2"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not dict(response.cookies)
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )
    assert await wait_for_blacklist_entry(key=f"revoked:{tokens.refresh_jti}")


async def test_update_password_requires_refresh_token(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Update password refuses a request that carries only an access token.

    The refresh token is what gets blacklisted after the change; if the
    route stopped requiring it, the response would still be 204 and the
    session's revocation would be silently skipped.
    """
    set_access_cookie(
        client=client,
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    response = await client.patch(
        url=app.url_path_for("access:update-password"),
        json={"currentPassword": "Test_Password2!", "newPassword": "New_Password@2"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Logout ---


async def test_logout(
    app: FastAPI,
    user_client_with_tokens: tuple[AsyncClient, SessionTokens],
    mocker: MockerFixture,
) -> None:
    """A single logout response covers cookies, blacklist, and cache."""
    client, tokens = user_client_with_tokens
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.utils.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await client.post(url=app.url_path_for("access:logout"))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not dict(response.cookies)
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )
    assert await wait_for_blacklist_entry(key=f"revoked:{tokens.refresh_jti}")


async def test_logout_requires_refresh_token(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Logout refuses a request that carries only an access token.

    The refresh token is what gets blacklisted on logout; if the
    route stopped requiring it, the response would still be 204 and
    the token's revocation would be silently skipped.
    """
    set_access_cookie(
        client=client,
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    response = await client.post(url=app.url_path_for("access:logout"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Account Retirement ---


async def test_delete_account(
    app: FastAPI,
    user_client_with_tokens: tuple[AsyncClient, SessionTokens],
    mocker: MockerFixture,
) -> None:
    """A single retirement response covers cookies, blacklist, and cache."""
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.utils.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    client, tokens = user_client_with_tokens
    response = await client.delete(url=app.url_path_for("access:delete-account"))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not dict(response.cookies)
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )
    assert await wait_for_blacklist_entry(key=f"revoked:{tokens.refresh_jti}")


async def test_delete_account_soft_deletes_the_user(
    app: FastAPI,
    user_client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Retirement is persisted: deleted_at set, is_active cleared.

    A 204 alone does not prove the write. The row is read back with include_deleted=True;
    the global soft-delete filter would otherwise hide it.
    """
    response = await user_client.delete(url=app.url_path_for("access:delete-account"))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    stmt = select(User).where(User.id == constants.USER_EXAMPLE_ID)
    user_obj = await session.scalar(stmt.execution_options(include_deleted=True))
    assert user_obj is not None
    assert user_obj.deleted_at is not None
    assert user_obj.is_active is False

    assert await wait_for_auth_context_eviction(user_id=constants.USER_EXAMPLE_ID)
    profile = await user_client.get(app.url_path_for("access:profile"))
    assert profile.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_account_rejects_default_system_admin(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """The default system admin cannot retire their own account.

    Deleting it would lock everyone out of the admin API with no recovery
    through the application.
    """
    client.cookies.set(
        name="access_token",
        value=create_access_token(
            user_id=constants.DEFAULT_ADMIN_ID,
            email=DEFAULT_ADMIN_EMAIL,
        ),
    )
    client.cookies.set(
        name="refresh_token",
        value=create_refresh_token(
            user_id=constants.DEFAULT_ADMIN_ID,
        ),
    )
    response = await client.delete(url=app.url_path_for("access:delete-account"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_account_requires_refresh_token(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """Delete account refuses a request that carries only an access token.

    The refresh token is what gets blacklisted on retirement; if the
    route stopped requiring it, the response would still be 204 and the
    session's revocation would be silently skipped.
    """
    set_access_cookie(
        client=client,
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    response = await client.delete(url=app.url_path_for("access:delete-account"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_account_keeps_email_reserved(
    app: FastAPI,
    client: AsyncClient,
    user_client: AsyncClient,
) -> None:
    """A retired account's email stays reserved until Job A anonymizes it.

    Retirement leaves the original email in the row, so the unique index
    still covers it. Job A is what later releases the address, rewriting
    it to deleted+<id>@anon.invalid.
    """
    response = await user_client.delete(url=app.url_path_for("access:delete-account"))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    re_register = await client.post(
        url=app.url_path_for("access:register"),
        json={
            "name": "Reclaimed",
            "email": constants.USER_EXAMPLE_EMAIL,
            "password": "Reclaimed&Pwd1",
            "confirmPassword": "Reclaimed&Pwd1",
        },
    )
    assert re_register.status_code == status.HTTP_409_CONFLICT


# --- Access Control ---


@pytest.mark.parametrize(
    ("path_name", "method"),
    [
        ("access:refresh", "post"),
        ("access:logout", "post"),
        ("access:update-password", "patch"),
        ("access:profile", "get"),
        ("access:delete-account", "delete"),
    ],
)
async def test_access_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    path_name: str,
    method: str,
) -> None:
    url = app.url_path_for(path_name)
    response = await getattr(client, method)(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
