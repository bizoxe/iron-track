from __future__ import annotations

import asyncio
from datetime import datetime  # noqa: TC003
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import Field

from app.domain.users.jwt_helpers import add_token_to_blacklist
from app.lib.exceptions import (
    PermissionDeniedException,
    UserNotFound,
)
from app.lib.filters import CommonFilters
from app.lib.invalidate_cache import invalidate_user_cache

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import StatementFilter

    from app.db.models.user import User as UserModel
    from app.domain.users.deps import UserServiceDep


async def check_user_before_modify_role(
    users_service: UserServiceDep,
    email: str,
) -> UserModel:
    """Check user existence and activity status before role modification.

    Args:
        users_service (UserService): Dependency for user service operations.
        email (str): The email of the user whose role is being modified.

    Returns:
        ~app.db.models.user.User: The User model object from the database.

    Raises:
        UserNotFound: If no user is found with the given email.
        PermissionDeniedException: If the user is found but their account is inactive.
    """
    user_obj = await users_service.get_one_or_none(email=email)
    if user_obj is None:
        raise UserNotFound
    if not user_obj.is_active:
        msg = f"Cannot modify role for inactive user {user_obj.email}"
        raise PermissionDeniedException(message=msg)

    return user_obj


async def perform_logout_cleanup(refresh_jti: str, user_id: UUID) -> None:
    """Perform asynchronous cleanup tasks upon user logout.

    This function is intended to be executed as a FastAPI background task
    to non-blocking revoke the refresh token and immediately invalidate
    cached user data.

    Args:
        refresh_jti (str): The JWT ID (JTI) of the refresh token to be blacklisted.
        user_id (UUID): The ID of the user whose cache needs to be invalidated.
    """
    await asyncio.gather(
        add_token_to_blacklist(
            refresh_token_identifier=refresh_jti,
        ),
        invalidate_user_cache(
            user_id=user_id,
        ),
    )


class UserFilters(CommonFilters):
    """Specific filters for User domain."""

    search_fields: ClassVar[set[str]] = {"name", "email"}
    order_by: Annotated[
        Literal["name", "email", "createdAt"],
        Field(description="Field to order by."),
    ] = "name"
    is_active: Annotated[
        bool | None,
        Field(description="Filter by active or inactive status."),
    ] = None
    created_before: Annotated[
        datetime | None,
        Field(description="Filter by created date before this timestamp."),
    ] = None
    created_after: Annotated[
        datetime | None,
        Field(description="Filter by created date after this timestamp."),
    ] = None

    @property
    def aa_technical_filters(self) -> list[StatementFilter]:
        filters = super().aa_technical_filters

        if self.created_after or self.created_before:
            filters.append(
                aa_filters.OnBeforeAfter(
                    field_name="created_at",
                    on_or_before=self.created_before,
                    on_or_after=self.created_after,
                )
            )
        if self.is_active is not None:
            filters.append(aa_filters.CollectionFilter(field_name="is_active", values=[self.is_active]))

        return filters
