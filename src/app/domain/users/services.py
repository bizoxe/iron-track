from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
)

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import (
    repository,
    service,
)
from advanced_alchemy.service import (
    ModelDictT,
    OffsetPagination,
    schema_dump,
)
from cashews import cache
from sqlalchemy.orm import load_only, noload, selectinload

from app.config.constants import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_USER_ROLE_SLUG,
)
from app.db import models as m
from app.domain.users.schemas import User as UserDto
from app.lib import crypt
from app.lib.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    UnauthorizedException,
)

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import StatementFilter

    from app.domain.users.schemas import PasswordUpdate


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class UserRepository(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = UserRepository
    match_fields: ClassVar[list[str]] = ["email"]

    default_role: ClassVar[str] = DEFAULT_USER_ROLE_SLUG
    system_admin_email: ClassVar[str] = DEFAULT_ADMIN_EMAIL

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        data = schema_dump(data)
        return await self._populate_with_hashed_password(data)

    async def to_model_on_update(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        data = schema_dump(data)
        return await self._populate_with_hashed_password(data)

    @staticmethod
    async def _populate_with_hashed_password(data: dict[str, Any]) -> dict[str, Any]:
        if (password := data.pop("password", None)) is not None:
            data["password"] = await crypt.get_password_hash(password=password)
        return data

    async def authenticate(self, username: str, password: str) -> m.User:
        """Authenticate a user.

        Args:
            username (str): User email.
            password (str): User password.

        Raises:
            UnauthorizedException: If the user is not found, not verified, or inactive.

        Returns:
            ~app.db.models.user.User: The user object.
        """
        db_obj = await self.get_one_or_none(
            email=username,
            load=[
                load_only(m.User.id, m.User.email, m.User.is_active, m.User.password),
                noload(m.User.role),
            ],
        )
        if (
            db_obj is None
            or not await crypt.verify_password(plain_password=password, hashed_password=db_obj.password)
            or not db_obj.is_active
        ):
            raise UnauthorizedException(message="Invalid credentials or account is unavailable")
        return db_obj

    async def update_password(self, data: PasswordUpdate, user_id: UUID) -> None:
        """Modify the stored user password.

        Args:
            data (PasswordUpdate): The Pydantic schema with current and new passwords.
            user_id (UUID): The unique ID of the target user.

        Raises:
            UnauthorizedException: If the current password is incorrect.
        """
        user_obj = await self.get(
            item_id=user_id,
            load=[
                load_only(m.User.id, m.User.password),
                noload(m.User.role),
            ],
        )
        if not await crypt.verify_password(data.current_password, user_obj.password):
            msg = "Current password is incorrect"
            raise UnauthorizedException(message=msg)
        user_obj.password = await crypt.get_password_hash(password=data.new_password)

    def check_critical_action_forbidden(
        self,
        target_user: m.User,
        calling_superuser_id: UUID,
    ) -> None:
        """Disallow destructive action on self or system admin.

        Args:
            target_user (:py:class:`~app.db.models.user.User`): The user object targeted for action.
            calling_superuser_id (UUID): UUID of the superuser calling the action.

        Raises:
            PermissionDeniedException: If target is the system admin or the caller themselves.
        """
        if target_user.email == self.system_admin_email:
            msg = "Forbidden: Cannot modify the primary system administrator account"
            raise PermissionDeniedException(message=msg)

        if target_user.id == calling_superuser_id:
            msg = "Self-action forbidden: Cannot perform destructive action on your own account"
            raise PermissionDeniedException(message=msg)

    @cache(ttl="1m", key="users_list:{filters}")
    async def get_users_paginated_dto(self, filters: list[StatementFilter]) -> OffsetPagination[UserDto]:
        """Retrieve a paginated list of users as DTOs."""
        results, total = await self.list_and_count(
            *filters,
            load=[
                selectinload(self.model_type.role).options(load_only(m.Role.name, m.Role.slug)),
            ],
        )
        return self.to_schema(data=results, total=total, filters=filters, schema_type=UserDto)


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for roles."""

    class RoleRepository(repository.SQLAlchemyAsyncRepository[m.Role]):
        """Role SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = RoleRepository
    match_fields: ClassVar[list[str]] = ["name"]

    async def get_id_and_slug_by_slug(self, slug: str) -> m.Role:
        """Retrieve the role object with column optimization."""
        try:
            return await self.get_one(
                slug=slug,
                load=load_only(self.model_type.id, self.model_type.slug),
            )
        except NotFoundError as exc:
            msg = f"Role with slug '{slug}' not found"
            raise NotFoundException(message=msg) from exc

    async def get_default_role(self, default_role_slug: str) -> m.Role:
        """Retrieve the default role object with column optimization.

        Args:
            default_role_slug (str): The slug of the default role (e.g., 'application-access').

        Returns:
            Role: A Role object (with `id`, `name`, and `slug` loaded).

        Raises:
            NotFoundError: Signals a **critical infrastructure failure**. This role is required,
                           and its absence means that the initial database seeding did not complete.
        """
        return await self.get_one(
            slug=default_role_slug,
            load=load_only(self.model_type.id, self.model_type.name, self.model_type.slug),
        )
