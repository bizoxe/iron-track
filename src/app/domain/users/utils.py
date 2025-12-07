from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.domain.users.jwt_helpers import add_token_to_blacklist
from app.lib.exceptions import (
    PermissionDeniedException,
    UserNotFound,
)
from app.lib.invalidate_cache import invalidate_user_cache

if TYPE_CHECKING:
    from uuid import UUID

    from app.db.models.user import User as UserModel
    from app.domain.users.deps import UserServiceDep
    from app.lib.deps import RedisClientDep


async def check_user_before_modify_role(
    users_service: UserServiceDep,
    email: str,
) -> UserModel:
    """Check user existence and activity status before a role modification operation.

    Args:
        users_service (UserService): Dependency for user service operations.
        email (str): The email of the user whose role is being modified.

    Returns:
        The User model object from the database.

    Raises:
        UserNotFound: If no user is found with the given email.
        BadRequestException: If the user is found but their account is inactive.
    """
    user_obj = await users_service.get_one_or_none(email=email)
    if user_obj is None:
        raise UserNotFound
    if not user_obj.is_active:
        msg = f"Cannot modify role for inactive user {user_obj.email}"
        raise PermissionDeniedException(message=msg)

    return user_obj


async def perform_logout_cleanup(refresh_jti: str, user_id: UUID, redis_client: RedisClientDep) -> None:
    """Perform necessary asynchronous cleanup tasks upon user logout.

    This function is intended to be executed as a FastAPI background task
    to non-blocking revoke the refresh token and immediately invalidate
    cached user data.

    Args:
        refresh_jti (str): The JWT ID (JTI) of the refresh token to be blacklisted.
        user_id (UUID): The ID of the user whose cache needs to be invalidated.
        redis_client (Redis): The Redis asynchronous client instance.
    """
    await asyncio.gather(
        add_token_to_blacklist(
            refresh_token_identifier=refresh_jti,
            redis_client=redis_client,
        ),
        invalidate_user_cache(
            user_id=user_id,
            redis_client=redis_client,
        ),
    )
