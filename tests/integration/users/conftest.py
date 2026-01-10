from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.domain.users.jwt_helpers import (
    create_access_token,
    create_refresh_token,
)
from tests import constants
from tests.helpers import (
    create_expired_access_token,
    create_expired_refresh_token,
)

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


@pytest.fixture(name="token_client")
def fx_client_with_tokens(
    client: AsyncClient,
) -> tuple[AsyncClient, dict[str, str]]:
    original_access_token = create_access_token(
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    original_refresh_token = create_refresh_token(
        user_id=constants.USER_EXAMPLE_ID,
    )
    client.cookies.set(name="access_token", value=original_access_token)
    client.cookies.set(name="refresh_token", value=original_refresh_token)

    return client, {
        "original_access_token": original_access_token,
        "original_refresh_token": original_refresh_token,
    }


@pytest.fixture(name="token_client_expired")
def fx_client_with_expired_tokens(client: AsyncClient) -> AsyncClient:
    access_expired = create_expired_access_token(
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    refresh_expired = create_expired_refresh_token(
        user_id=constants.USER_EXAMPLE_ID,
    )
    client.cookies.set(name="access_token", value=access_expired)
    client.cookies.set(name="refresh_token", value=refresh_expired)

    return client
