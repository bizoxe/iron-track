from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from cashews import cache

from app.config.base import get_settings
from app.domain.accounts.jwt_helpers import add_token_to_blacklist
from app.lib.exceptions import PermissionDeniedException

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models.user import User as UserModel
    from app.domain.accounts.schemas import UserAuth


async def invalidate_user_cache(user_id: UUID) -> None:
    """Invalidate the cached data for a user by ID."""
    await cache.delete(key=f"user_auth:{user_id}")


def check_critical_action_forbidden(
    target_user: UserModel,
    calling_superuser_id: UUID,
    admin_email: str = get_settings().app.DEFAULT_ADMIN_EMAIL,
) -> None:
    """Disallow destructive action on self or system admin.

    Args:
        target_user (:py:class:`~app.db.models.user.User`): The user object targeted for action.
        calling_superuser_id (UUID): UUID of the superuser calling the action.
        admin_email (str): Email address of the primary system administrator.

    Raises:
        PermissionDeniedException: If target is the system admin or the caller themselves.
    """
    if target_user.email == admin_email:
        msg = "Forbidden: Cannot modify the primary system administrator account"
        raise PermissionDeniedException(message=msg)

    if target_user.id == calling_superuser_id:
        msg = "Self-action forbidden: Cannot perform destructive action on your own account"
        raise PermissionDeniedException(message=msg)


def get_refresh_context(user_auth: UserAuth) -> tuple[str, float]:
    """Validate that the user authentication context contains refresh metadata."""
    jti = user_auth._refresh_jti  # noqa: SLF001
    exp = user_auth._refresh_exp  # noqa: SLF001
    if jti is None or exp is None:
        msg = "UserAuth context missing refresh token metadata"
        raise ValueError(msg)
    return jti, exp


async def perform_logout_cleanup(refresh_jti: str, ttl: int, user_id: UUID) -> None:
    """Perform asynchronous cleanup tasks upon user logout.

    Executed as a FastAPI background task to non-blockingly revoke the refresh token
    in cache and invalidate cached user data.

    Args:
        refresh_jti (str): The JWT ID (JTI) of the refresh token to be blacklisted.
        ttl (int): The time-to-live duration in seconds for token invalidation.
        user_id (UUID): The ID of the user whose cache needs to be invalidated.
    """
    await asyncio.gather(
        add_token_to_blacklist(
            refresh_token_identifier=refresh_jti,
            ttl=ttl,
        ),
        invalidate_user_cache(
            user_id=user_id,
        ),
    )
