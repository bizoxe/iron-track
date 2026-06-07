from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.config.base import get_settings
from app.domain.users.jwt_helpers import add_token_to_blacklist
from app.lib.exceptions import PermissionDeniedException
from app.lib.invalidate_cache import invalidate_user_cache

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models.user import User as UserModel
    from app.domain.users.schemas import UserAuth


def check_critical_action_forbidden(
    target_user: UserModel,
    calling_superuser_id: UUID,
) -> None:
    """Disallow destructive action on self or system admin.

    Args:
        target_user (:py:class:`~app.db.models.user.User`): The user object targeted for action.
        calling_superuser_id (UUID): UUID of the superuser calling the action.

    Raises:
        PermissionDeniedException: If target is the system admin or the caller themselves.
    """
    if target_user.email == get_settings().app.DEFAULT_ADMIN_EMAIL:
        msg = "Forbidden: Cannot modify the primary system administrator account"
        raise PermissionDeniedException(message=msg)

    if target_user.id == calling_superuser_id:
        msg = "Self-action forbidden: Cannot perform destructive action on your own account"
        raise PermissionDeniedException(message=msg)


async def perform_logout_cleanup(refresh_jti: str, ttl: int, user_id: UUID) -> None:
    """Perform asynchronous cleanup tasks upon user logout.

    This function is intended to be executed as a FastAPI background task
    to non-blocking revoke the refresh token in cache with a specified TTL
    and immediately invalidate cached user data.

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


def get_refresh_context(user_auth: UserAuth) -> tuple[str, float]:
    """Validate that the user authentication context contains refresh metadata."""
    jti = user_auth._refresh_jti  # noqa: SLF001
    exp = user_auth._refresh_exp  # noqa: SLF001
    if jti is None or exp is None:
        msg = "UserAuth context missing refresh token metadata"
        raise ValueError(msg)
    return jti, exp
