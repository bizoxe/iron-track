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

from src.config.app_settings import DatabaseSession  # noqa: TC001
from src.db.models.role import Role as RoleModel
from src.db.models.user import User as UserModel
from src.domain.users.services import (
    RoleService,
    UserService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def provide_users_service(db_session: DatabaseSession) -> AsyncGenerator[UserService, None]:
    """Provide a new, scoped instance of the UserService."""
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
    """Provide a new, scoped instance of the RoleService."""
    async with RoleService.new(
        session=db_session,
    ) as service:
        yield service


RoleServiceDep = Annotated[RoleService, Depends(provide_role_service)]
