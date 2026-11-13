from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import select

from app.config.constants import (
    DEFAULT_USER_ROLE_SLUG,
    FITNESS_TRAINER_ROLE_SLUG,
    SUPERUSER_ROLE_SLUG,
)
from app.db.models.role import Role
from app.db.models.user import User
from tests import constants

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx2 import AsyncClient
    from pytest_mock import MockerFixture
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio

# --- Helpers ---


async def fetch_user(session: AsyncSession, user_id: UUID) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await session.scalar(stmt)
    assert result is not None
    return result


async def fetch_role_id_by_slug(session: AsyncSession, slug: str) -> UUID:
    stmt = select(Role.id).where(Role.slug == slug)
    result = await session.scalar(stmt)
    assert result is not None
    return result


# --- Assign and Revoke User Role ---


@pytest.mark.parametrize(
    ("user_id", "role_slug", "status_code"),
    [
        pytest.param(
            constants.USER_EXAMPLE_ID,
            SUPERUSER_ROLE_SLUG,
            status.HTTP_200_OK,
            id="assign_superuser_role",
        ),
        pytest.param(
            constants.ANOTHER_USER_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_200_OK,
            id="assign_fitness_trainer_role",
        ),
        pytest.param(
            UUID("019a643e-db0a-77d0-89a6-0536f6d00a99"),
            SUPERUSER_ROLE_SLUG,
            status.HTTP_404_NOT_FOUND,
            id="user_not_found",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_409_CONFLICT,
            id="user_already_has_role",
        ),
        pytest.param(
            constants.INACTIVE_USER_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="inactive_user",
        ),
        pytest.param(
            constants.SUPERUSER_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="self_action_forbidden",
        ),
        pytest.param(
            constants.DEFAULT_ADMIN_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="action_on_system_admin_forbidden",
        ),
    ],
)
async def test_assign_new_role(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    role_slug: str,
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", user_id=user_id),
        json={"roleSlug": role_slug},
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        assert response.json()["details"]["user_id"] == str(user_id)
        assert response.json()["details"]["role_slug"] == role_slug


async def test_assign_new_role_cache_invalidated(
    app: FastAPI,
    superuser_client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.controllers.user_roles.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", user_id=constants.USER_EXAMPLE_ID),
        json={"roleSlug": FITNESS_TRAINER_ROLE_SLUG},
    )
    assert response.status_code == status.HTTP_200_OK
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.USER_EXAMPLE_ID,
    )


@pytest.mark.parametrize(
    ("user_id", "role_slug", "status_code"),
    [
        pytest.param(
            constants.FITNESS_TRAINER_ID,
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_200_OK,
            id="role_revoked",
        ),
        pytest.param(
            constants.FITNESS_TRAINER_ID,
            SUPERUSER_ROLE_SLUG,
            status.HTTP_409_CONFLICT,
            id="revoked_role_mismatch",
        ),
        pytest.param(
            UUID("019a643e-db0a-77d0-89a6-0536f6d00a99"),
            FITNESS_TRAINER_ROLE_SLUG,
            status.HTTP_404_NOT_FOUND,
            id="user_not_found",
        ),
        pytest.param(
            constants.INACTIVE_USER_ID,
            SUPERUSER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="inactive_user",
        ),
        pytest.param(
            constants.SUPERUSER_ID,
            SUPERUSER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="self_action_forbidden",
        ),
        pytest.param(
            constants.DEFAULT_ADMIN_ID,
            SUPERUSER_ROLE_SLUG,
            status.HTTP_403_FORBIDDEN,
            id="action_on_system_admin_forbidden",
        ),
    ],
)
async def test_revoke_and_set_default_role(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_id: UUID,
    role_slug: str,
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", user_id=user_id),
        json={"roleSlug": role_slug},
    )
    assert response.status_code == status_code
    if response.status_code == status.HTTP_200_OK:
        assert response.json()["details"]["user_id"] == str(user_id)
        assert response.json()["details"]["revoked_role"] == role_slug
        assert response.json()["details"]["default_role"] == DEFAULT_USER_ROLE_SLUG


async def test_revoke_and_set_default_role_cache_invalidated(
    app: FastAPI,
    superuser_client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    mock_invalidate_cache = mocker.patch(
        "app.domain.accounts.controllers.user_roles.invalidate_user_cache",
        new_callable=mocker.AsyncMock,
    )
    response = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", user_id=constants.FITNESS_TRAINER_ID),
        json={"roleSlug": FITNESS_TRAINER_ROLE_SLUG},
    )
    assert response.status_code == status.HTTP_200_OK
    mock_invalidate_cache.assert_called_once_with(
        user_id=constants.FITNESS_TRAINER_ID,
    )


# --- Scenario Tests ---


async def test_role_lifecycle_updates_role_and_flag(
    app: FastAPI,
    superuser_client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Each role transition persists the role id and the mirror flag.

    The lifecycle deliberately demotes twice: through assign (superuser
    given a lesser role — the flag must drop in place) and through revoke
    (any role reset to the default). A lifecycle that only ever promotes
    and revokes would never notice assign_role forgetting the flag.
    """
    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", user_id=constants.USER_EXAMPLE_ID),
        json={"roleSlug": SUPERUSER_ROLE_SLUG},
    )
    assert response.status_code == status.HTTP_200_OK
    expected_role_id = await fetch_role_id_by_slug(session, SUPERUSER_ROLE_SLUG)
    user_obj = await fetch_user(session, constants.USER_EXAMPLE_ID)
    assert user_obj.role_id == expected_role_id
    assert user_obj.is_superuser is True

    response = await superuser_client.patch(
        url=app.url_path_for("roles:assign", user_id=constants.USER_EXAMPLE_ID),
        json={"roleSlug": FITNESS_TRAINER_ROLE_SLUG},
    )
    assert response.status_code == status.HTTP_200_OK
    expected_role_id = await fetch_role_id_by_slug(session, FITNESS_TRAINER_ROLE_SLUG)
    user_obj = await fetch_user(session, constants.USER_EXAMPLE_ID)
    assert user_obj.role_id == expected_role_id
    assert user_obj.is_superuser is False

    response = await superuser_client.patch(
        url=app.url_path_for("roles:revoke", user_id=constants.USER_EXAMPLE_ID),
        json={"roleSlug": FITNESS_TRAINER_ROLE_SLUG},
    )
    assert response.status_code == status.HTTP_200_OK
    expected_role_id = await fetch_role_id_by_slug(session, DEFAULT_USER_ROLE_SLUG)
    user_obj = await fetch_user(session, constants.USER_EXAMPLE_ID)
    assert user_obj.role_id == expected_role_id
    assert user_obj.is_superuser is False


async def test_assign_role_changes_access_end_to_end(
    app: FastAPI,
    superuser_client: AsyncClient,
    user_client: AsyncClient,
) -> None:
    """A newly assigned role takes effect on the target user's live session.

    The cached UserAuth keeps the previous role until its TTL expires;
    without the invalidation in the assign route the second request
    would still be refused.
    """
    assert (await user_client.get(app.url_path_for("users:list"))).status_code == status.HTTP_403_FORBIDDEN

    promoted = await superuser_client.patch(
        url=app.url_path_for("roles:assign", user_id=constants.USER_EXAMPLE_ID),
        json={"roleSlug": SUPERUSER_ROLE_SLUG},
    )
    assert promoted.status_code == status.HTTP_200_OK

    assert (await user_client.get(app.url_path_for("users:list"))).status_code == status.HTTP_200_OK


# --- Access Control ---


@pytest.mark.parametrize("url_name", ["roles:assign", "roles:revoke"])
async def test_user_role_routes_require_superuser(
    app: FastAPI,
    user_client: AsyncClient,
    url_name: str,
) -> None:
    url = app.url_path_for(url_name, user_id=constants.USER_EXAMPLE_ID)
    response = await user_client.patch(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("url_name", ["roles:assign", "roles:revoke"])
async def test_user_role_routes_require_authentication(
    app: FastAPI,
    client: AsyncClient,
    url_name: str,
) -> None:
    url = app.url_path_for(url_name, user_id=constants.USER_EXAMPLE_ID)
    response = await client.patch(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
