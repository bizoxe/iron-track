from typing import TYPE_CHECKING

import pytest
from fastapi import status

from app.config.constants import DEFAULT_ADMIN_EMAIL
from tests import constants

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from pytest_mock import MockerFixture
    from redis.asyncio import Redis

pytestmark = pytest.mark.anyio

# --- Basic & Integration Tests ---


@pytest.mark.parametrize(
    ("email", "role_slug", "status_code"),
    [
        pytest.param(
            "non.exists@example.com",
            "superuser",
            status.HTTP_404_NOT_FOUND,
            id="error_user_not_found",
        ),
        pytest.param(
            constants.INACTIVE_USER_EMAIL,
            "superuser",
            status.HTTP_403_FORBIDDEN,
            id="error_inactive_user",
        ),
        pytest.param(
            constants.SUPERUSER_EMAIL,
            "fitness-trainer",
            status.HTTP_403_FORBIDDEN,
            id="error_self_action_forbidden",
        ),
        pytest.param(
            DEFAULT_ADMIN_EMAIL,
            "fitness-trainer",
            status.HTTP_403_FORBIDDEN,
            id="error_action_on_system_admin",
        ),
        pytest.param(
            constants.USER_EXAMPLE_EMAIL,
            "superuser",
            status.HTTP_200_OK,
            id="success_assign_superuser_role",
        ),
        pytest.param(
            constants.ANOTHER_USER_EMAIL,
            "fitness-trainer",
            status.HTTP_200_OK,
            id="success_assign_trainer_role",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_EMAIL,
            "fitness-trainer",
            status.HTTP_409_CONFLICT,
            id="error_user_already_has_role",
        ),
        pytest.param(
            constants.USER_EXAMPLE_EMAIL,
            "stub",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            id="error_invalid_role_slug",
        ),
    ],
)
async def test_assign_new_role(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    email: str,
    role_slug: str,
    status_code: int,
    mocker: "MockerFixture",
) -> None:
    _ = mocker.patch(
        "app.domain.users.controllers.user_role.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", email=email),
        json={"role_slug": role_slug},
    )
    assert response.status_code == status_code


async def test_assign_new_role_cache_invalidated(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    mocker: "MockerFixture",
    redis_client: "Redis",
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.controllers.user_role.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", email=constants.USER_EXAMPLE_EMAIL),
        json={"role_slug": "fitness-trainer"},
    )
    assert response.status_code == status.HTTP_200_OK
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
        redis_client=redis_client,
    )
    response_data = response.json()
    success_msg = response_data["message"]
    assert success_msg == f"Successfully assigned the '{'fitness-trainer'}' role to {constants.USER_EXAMPLE_EMAIL}"


@pytest.mark.parametrize(
    ("email", "role_slug", "status_code"),
    [
        pytest.param(
            "non.exists@example.com",
            "fitness-trainer",
            status.HTTP_404_NOT_FOUND,
            id="error_user_not_found",
        ),
        pytest.param(
            constants.INACTIVE_USER_EMAIL,
            "fitness-trainer",
            status.HTTP_403_FORBIDDEN,
            id="error_inactive_user",
        ),
        pytest.param(
            constants.SUPERUSER_EMAIL,
            "superuser",
            status.HTTP_403_FORBIDDEN,
            id="error_self_action_forbidden",
        ),
        pytest.param(
            DEFAULT_ADMIN_EMAIL,
            "superuser",
            status.HTTP_403_FORBIDDEN,
            id="error_action_on_system_admin",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_EMAIL,
            "fitness-trainer",
            status.HTTP_200_OK,
            id="success_role_revoked",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_EMAIL,
            "superuser",
            status.HTTP_409_CONFLICT,
            id="error_role_not_match",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_EMAIL,
            "stub",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            id="error_invalid_role_slug",
        ),
    ],
)
async def test_revoke_and_set_default_role(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    email: str,
    role_slug: str,
    status_code: int,
    mocker: "MockerFixture",
) -> None:
    _ = mocker.patch(
        "app.domain.users.controllers.user_role.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", email=email),
        json={"role_slug": role_slug},
    )
    assert response.status_code == status_code


async def test_revoke_and_set_default_role_cache_invalidated(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    redis_client: "Redis",
    mocker: "MockerFixture",
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.users.controllers.user_role.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", email=constants.FITNESS_TRAINER_EMAIL),
        json={"role_slug": "fitness-trainer"},
    )
    assert response.status_code == status.HTTP_200_OK
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.FITNESS_TRAINER_ID,
        redis_client=redis_client,
    )


@pytest.mark.parametrize(
    "url_name",
    [
        "roles:assign",
        "roles:revoke",
    ],
)
async def test_role_management_forbidden_for_regular_user(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_name: str,
) -> None:
    url = app.url_path_for(url_name, email=constants.USER_EXAMPLE_EMAIL)
    response = await user_client.patch(url, json={})
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- Scenario Tests (Multi-step Flows) ---


async def test_assign_and_revoke_role(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    mocker: "MockerFixture",
) -> None:
    role_to_assign = "superuser"
    role_to_revoke_incorrect = "fitness-trainer"
    role_to_revoke = role_to_assign
    default_role = "application-access"
    _ = mocker.patch(
        "app.domain.users.controllers.user_role.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", email=constants.USER_EXAMPLE_EMAIL),
        json={"role_slug": role_to_assign},
    )
    assert response.status_code == status.HTTP_200_OK
    response_revoke_conflict = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", email=constants.USER_EXAMPLE_EMAIL),
        json={"role_slug": role_to_revoke_incorrect},
    )
    assert response_revoke_conflict.status_code == status.HTTP_409_CONFLICT
    revoke_conflict_data = response_revoke_conflict.json()
    msg_conflict = revoke_conflict_data["detail"]
    msg_expected = (
        f"User {constants.USER_EXAMPLE_EMAIL} currently has the '{role_to_assign}' role, "
        f"which does not match the requested role '{role_to_revoke_incorrect}' for revocation"
    )
    assert msg_conflict == msg_expected
    response_revoke = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", email=constants.USER_EXAMPLE_EMAIL),
        json={"role_slug": role_to_revoke},
    )
    assert response_revoke.status_code == status.HTTP_200_OK
    response_revoke_data = response_revoke.json()
    msg_expected_success = (
        f"Successfully revoked the '{role_to_revoke}' role for {constants.USER_EXAMPLE_EMAIL} "
        f"and set to default role '{default_role}'"
    )
    success_msg = response_revoke_data["message"]
    assert success_msg == msg_expected_success
