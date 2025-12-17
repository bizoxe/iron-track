from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
)

from fastapi import Depends
from sqlalchemy.orm import (
    load_only,
    selectinload,
)

from app.config.app_settings import DatabaseSession  # noqa: TC001
from app.db.models.role import Role as RoleModel
from app.db.models.user import User as UserModel
from app.domain.users.services import (
    RoleService,
    UserService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def provide_users_service(db_session: DatabaseSession) -> AsyncGenerator[UserService, None]:
    """Provide a new, scoped instance of the UserService.

    Args:
        db_session (DatabaseSession): The current database session.

    Yields:
        UserService: The new service instance.
    """
    async with UserService.new(
        session=db_session,
        load=[
            selectinload(UserModel.role).options(load_only(RoleModel.name, RoleModel.slug)),
        ],
        error_messages={"duplicate_key": "This user already exists.", "integrity": "User operation failed."},
    ) as service:
        yield service


UserServiceDep = Annotated[UserService, Depends(provide_users_service)]


async def provide_role_service(db_session: DatabaseSession) -> AsyncGenerator[RoleService, None]:
    """Provide a new, scoped instance of the RoleService.

    Args:
        db_session (DatabaseSession): The current database session.

    Yields:
        RoleService: The new service instance.
    """
    async with RoleService.new(
        session=db_session,
    ) as service:
        yield service


RoleServiceDep = Annotated[RoleService, Depends(provide_role_service)]
