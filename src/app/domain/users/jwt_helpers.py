from datetime import timedelta
from typing import TYPE_CHECKING

from cashews import cache

from app.config.base import get_settings
from app.config.constants import REFRESH_TOKEN_MAX_AGE
from app.lib.jwt_utils import encode_jwt

if TYPE_CHECKING:
    from uuid import UUID


settings = get_settings()


def create_access_token(
    user_id: "UUID",
    email: str,
) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id (UUID): The unique identifier of the user.
        email (str): The user's email address.

    Returns:
        str: The encoded access token string.
    """
    jwt_payload = {
        "sub": str(user_id),
        "email": email,
    }
    return encode_jwt(payload=jwt_payload)


def create_refresh_token(user_id: "UUID") -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id (UUID): The unique identifier of the user.

    Returns:
        str: The encoded refresh token string.
    """
    jwt_payload = {
        "sub": str(user_id),
    }
    return encode_jwt(
        payload=jwt_payload,
        expire_timedelta=timedelta(
            days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )


async def add_token_to_blacklist(refresh_token_identifier: str) -> None:
    """Add a refresh token identifier (JTI) to Redis for revocation."""
    await cache.set(
        key=f"revoked:{refresh_token_identifier}",
        value="1",
        expire=REFRESH_TOKEN_MAX_AGE,
    )


async def is_token_in_blacklist(refresh_token_identifier: str) -> bool:
    """Check if a refresh token identifier (JTI) exists in the blacklist."""
    return await cache.exists(f"revoked:{refresh_token_identifier}")
