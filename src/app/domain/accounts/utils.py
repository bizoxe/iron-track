from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from cashews import cache

from app.config.constants import DEFAULT_ADMIN_EMAIL, USER_AUTH_CACHE_KEY_PREFIX
from app.domain.accounts.jwt_helpers import add_token_to_blacklist
from app.lib.exceptions import PermissionDeniedException

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models.user import User as UserModel


async def invalidate_user_cache(user_id: UUID) -> None:
    """Invalidate the cached data for a user by ID."""
    await cache.delete(key=f"{USER_AUTH_CACHE_KEY_PREFIX}:{user_id}")


def check_critical_action_forbidden(
    target_user: UserModel,
    calling_superuser_id: UUID,
    admin_email: str = DEFAULT_ADMIN_EMAIL,
) -> None:
    """Disallow destructive action on self or system admin.

    Intended for admin-surface handlers: the caller acts on another account.
    Self-service paths enforce their own guards (see retire).

    Args:
        target_user (:py:class:`~app.db.models.user.User`): The user object targeted for action.
        calling_superuser_id (UUID): UUID of the superuser calling the action.
        admin_email (str): Email address of the primary system administrator.

    Raises:
        PermissionDeniedException: If target is the system admin or the caller themselves.
    """
    if target_user.email == admin_email:
        msg = "Cannot modify the primary system administrator account"
        raise PermissionDeniedException(message=msg)

    if target_user.id == calling_superuser_id:
        msg = "Cannot perform destructive action on your own account"
        raise PermissionDeniedException(message=msg)


async def perform_logout_cleanup(refresh_jti: str, ttl: int, user_id: UUID) -> None:
    """Perform asynchronous cleanup tasks upon user logout.

    Executed as a FastAPI background task to non-blockingly revoke the refresh token
    in cache and invalidate cached user data. The auth cache is dropped so the
    next session rebuilds the auth context from the database — including any
    UserAuth copies the refresh flow may have mutated with its jti/exp pair.

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
