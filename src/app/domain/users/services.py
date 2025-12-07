from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import (
    repository,
    service,
)
from advanced_alchemy.service import (
    ModelDictT,
    is_dict,
    schema_dump,
)
from sqlalchemy.orm import load_only

from app.config.constants import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_USER_ROLE_SLUG,
)
from app.db import models as m
from app.lib import crypt
from app.lib.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    UnauthorizedException,
)

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.users.schemas import PasswordUpdate


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class UserRepository(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = UserRepository
    default_role = DEFAULT_USER_ROLE_SLUG
    system_admin_email = DEFAULT_ADMIN_EMAIL
    match_fields = ["email"]  # noqa: RUF012

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        data = schema_dump(data)
        return await self._populate_with_hashed_password(data)

    async def to_model_on_update(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        data = schema_dump(data)
        return await self._populate_with_hashed_password(data)

    async def _populate_with_hashed_password(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await crypt.get_password_hash(password=password)
        return data

    async def authenticate(self, username: str, password: str | bytes) -> m.User:
        """Authenticate a user.

        Args:
            username (str): User email
            password (str | bytes): User password

        Raises:
            UnauthorizedException: Raised when the user doesn't exist, isn't verified, or is not active.

        Returns:
            User: The user object.
        """
        db_obj = await self.get_one_or_none(email=username)
        if (
            db_obj is None
            or not await crypt.verify_password(password=password, hashed_password=db_obj.hashed_password)
            or not db_obj.is_active
        ):
            raise UnauthorizedException(message="Invalid credentials or account is unavailable")

        return db_obj

    async def update_password(self, data: PasswordUpdate, user_id: UUID) -> None:
        """Modify stored user auth password."""
        user_obj = await self.get(user_id)
        if not await crypt.verify_password(data.current_password, user_obj.hashed_password):
            msg = "Current password is incorrect"
            raise UnauthorizedException(message=msg)
        user_obj.hashed_password = await crypt.get_password_hash(data.new_password)

    def check_critical_action_forbidden(
        self,
        target_user: m.User,
        calling_superuser_id: UUID,
    ) -> None:
        """Disallow destructive action on self or system admin."""
        if target_user.email == self.system_admin_email:
            msg = "Forbidden: Cannot modify the primary system administrator account"
            raise PermissionDeniedException(message=msg)

        if target_user.id == calling_superuser_id:
            msg = "Self-action forbidden: Cannot perform destructive action on your own account"
            raise PermissionDeniedException(message=msg)


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for users."""

    class RoleRepository(repository.SQLAlchemyAsyncRepository[m.Role]):
        """User SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = RoleRepository
    match_fields = ["name"]  # noqa: RUF012

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
            A Role object (with `id`, `name`, and `slug` loaded).

        Raises:
            NotFoundError: Signals a **critical infrastructure failure**. This role is required,
                            and its absence means that the initial database seeding did not complete.
        """
        return await self.get_one(
            slug=default_role_slug,
            load=load_only(self.model_type.id, self.model_type.name, self.model_type.slug),
        )
