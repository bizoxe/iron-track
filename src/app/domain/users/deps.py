from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
)

from fastapi import Depends

from app.config.app_settings import DatabaseSession  # noqa: TC001
from app.domain.users.services import (
    RoleService,
    UserService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def provide_users_service(db_session: DatabaseSession) -> AsyncGenerator[UserService, None]:
    """Provide a new, scoped instance of the UserService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        UserService: The new service instance.
    """
    async with UserService.new(
        session=db_session,
        error_messages={"duplicate_key": "This user already exists.", "integrity": "User operation failed."},
    ) as service:
        yield service


UserServiceDep = Annotated[UserService, Depends(provide_users_service)]


async def provide_role_service(db_session: DatabaseSession) -> AsyncGenerator[RoleService, None]:
    """Provide a new, scoped instance of the RoleService.

    Args:
        db_session (AsyncSession): The current database session.

    Yields:
        RoleService: The new service instance.
    """
    async with RoleService.new(
        session=db_session,
    ) as service:
        yield service


RoleServiceDep = Annotated[RoleService, Depends(provide_role_service)]
