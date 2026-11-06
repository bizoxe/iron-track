from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import repository, service
from advanced_alchemy.service import OffsetPagination, schema_dump
from cashews import cache
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, load_only, noload

from app.config.constants import DEFAULT_ADMIN_EMAIL, SUPERUSER_ROLE_SLUG
from app.db import models as m
from app.domain.accounts.schemas import User as UserDto
from app.domain.accounts.schemas import UserPage
from app.domain.accounts.utils import check_critical_action_forbidden
from app.lib import crypt
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    UnauthorizedException,
    UserNotFound,
)

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

    from app.domain.accounts.filters import UserFilters
    from app.domain.accounts.schemas import PasswordUpdate


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for users."""

    class UserRepository(repository.SQLAlchemyAsyncRepository[m.User]):
        """User SQLAlchemy Repository."""

        model_type = m.User

    repository_type = UserRepository
    match_fields: ClassVar[list[str]] = ["email"]

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        return await self._populate_with_hashed_password(schema_dump(data))

    async def authenticate(self, username: str, password: str) -> m.User:
        """Authenticate a user.

        Args:
            username (str): User email.
            password (str): User password.

        Raises:
            UnauthorizedException: If the user is not found, the password is incorrect,
                or the account is inactive or soft-deleted.

        Returns:
            ~app.db.models.user.User: The user object.
        """
        statement = select(self.model_type).where(func.lower(self.model_type.email) == username.lower())
        user_obj = await self.get_one_or_none(
            statement=statement,
            load=[
                load_only(
                    self.model_type.id,
                    self.model_type.email,
                    self.model_type.is_active,
                    self.model_type.password,
                    self.model_type.deleted_at,
                ),
                noload(self.model_type.role),
            ],
        )
        # Cheap rejections first: inactive/soft-deleted accounts must never
        # reach verify_password — the anonymized sentinel hash ('!purged') is
        # not a valid argon2 hash and would poison verify_and_update.
        if (
            user_obj is None
            or not (user_obj.is_active and user_obj.deleted_at is None)
            or not await crypt.verify_password(plain_password=password, hashed_password=user_obj.password)
        ):
            raise UnauthorizedException(message="Invalid credentials or account is unavailable")
        return user_obj

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
                load_only(self.model_type.id, self.model_type.password),
                noload(self.model_type.role),
            ],
        )
        if not await crypt.verify_password(data.current_password, user_obj.password):
            msg = "Current password is incorrect"
            raise UnauthorizedException(message=msg)
        user_obj.password = await crypt.get_password_hash(password=data.new_password)

    async def update_user(self, data: dict[str, Any], user_id: UUID, superuser_id: UUID) -> m.User:
        """Update user attributes with security checks and conflict handling.

        Ensures critical security rules and system constraints are enforced
        during the update process.

        Raises:
            UserNotFound: If the user with the specified ID does not exist.
            PermissionDeniedException: If attempting to modify the system admin or self.
            ConflictException: If the updated email is already taken by another user.
        """
        try:
            user_obj = await self.get(
                user_id,
                load=[
                    joinedload(self.model_type.role, innerjoin=True).load_only(m.Role.name, m.Role.slug),
                ],
            )
        except NotFoundError as exc:
            raise UserNotFound from exc

        check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=superuser_id,
        )
        await self._populate_with_hashed_password(data=data)
        for field, value in data.items():
            setattr(user_obj, field, value)

        try:
            await self.repository.session.flush()
        except IntegrityError as exc:
            msg = "A user with this email is already registered in the system"
            raise ConflictException(message=msg) from exc
        return user_obj

    async def retire(self, user_id: UUID) -> None:
        """Retire the user account (soft delete).

        Disallows retiring the primary system administrator account.

        Raises:
            PermissionDeniedException: If the account is the primary system administrator.
        """
        user_obj = await self.get(
            user_id,
            load=[
                load_only(self.model_type.id, self.model_type.email),
                noload(self.model_type.role),
            ],
        )

        if user_obj.email == DEFAULT_ADMIN_EMAIL:
            msg = "The primary system administrator account cannot be deleted"
            raise PermissionDeniedException(message=msg)

        user_obj.deleted_at = datetime.now(tz=UTC)
        user_obj.is_active = False

    async def get_users_paginated_dto(self, params: UserFilters) -> OffsetPagination[UserDto]:
        """Provide a filtered and paginated list of users with caching."""
        page = await self._get_users_page(params)
        return OffsetPagination(items=page.items, total=page.total, limit=page.limit, offset=page.offset)

    async def get_and_validate_for_role_change(self, user_id: UUID) -> m.User:
        """Retrieve an active user by ID for role modification.

        Args:
            user_id (UUID): The ID of the user whose role is being modified.

        Returns:
            ~app.db.models.user.User: The User model object from the database.

        Raises:
            UserNotFound: If no user is found with the given ID.
            PermissionDeniedException: If the user is found but their account is inactive.
        """
        user_obj = await self.get_one_or_none(
            id=user_id,
            load=[
                load_only(
                    self.model_type.id,
                    self.model_type.is_active,
                    self.model_type.is_superuser,
                    self.model_type.email,
                    self.model_type.role_id,
                ),
                noload(self.model_type.role),
            ],
        )
        if user_obj is None:
            raise UserNotFound
        if not user_obj.is_active:
            msg = "Cannot modify role for inactive user"
            raise PermissionDeniedException(message=msg)

        return user_obj

    @staticmethod
    def assign_role(user_obj: m.User, new_role: m.Role) -> None:
        """Apply a new role and keep the superuser flag in sync."""
        if new_role.slug == SUPERUSER_ROLE_SLUG:
            user_obj.is_superuser = True
        if user_obj.is_superuser and new_role.slug != SUPERUSER_ROLE_SLUG:
            user_obj.is_superuser = False
        user_obj.role_id = new_role.id

    @staticmethod
    def revoke_role(user_obj: m.User, default_role: m.Role) -> None:
        """Reset the user to the default role and clear the superuser flag."""
        user_obj.is_superuser = False
        user_obj.role_id = default_role.id

    @staticmethod
    async def _populate_with_hashed_password(data: dict[str, Any]) -> dict[str, Any]:
        if "password" in data:
            data["password"] = await crypt.get_password_hash(password=data["password"])
        return data

    # TTL-only by design: user mutations do not invalidate cached pages.
    @cache(ttl="1m", key="users_list:{params}")
    async def _get_users_page(self, params: UserFilters) -> UserPage:
        """Fetch and cache a user page as a plain envelope."""
        filters = params.as_aa_filters
        results, total = await self.get_many_and_count(
            *filters,
            load=[
                joinedload(self.model_type.role, innerjoin=True).load_only(m.Role.name, m.Role.slug),
            ],
            execution_options={"include_deleted": True},
        )
        pagination = self.to_schema(data=results, total=total, filters=filters, schema_type=UserDto)
        return UserPage(
            items=pagination.items, total=pagination.total, limit=pagination.limit, offset=pagination.offset
        )


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for roles."""

    class RoleRepository(repository.SQLAlchemyAsyncRepository[m.Role]):
        """Role SQLAlchemy Repository."""

        model_type = m.Role

    repository_type = RoleRepository
    match_fields: ClassVar[list[str]] = ["name"]

    async def get_default_role(self, default_role_slug: str) -> m.Role:
        """Retrieve the default role object with column optimization.

        Args:
            default_role_slug (str): The slug of the default role.

        Returns:
            Role: A Role object (with `id`, `name`, and `slug` loaded).

        Raises:
            NotFoundError: Signals a critical infrastructure failure. This role is required,
                and its absence means that the initial database seeding did not complete.
        """
        return await self.get_one(
            slug=default_role_slug,
            load=load_only(self.model_type.id, self.model_type.name, self.model_type.slug),
        )

    async def get_id_and_slug_by_slug(self, slug: str) -> m.Role:
        """Retrieve the role object with column optimization.

        Raises:
            NotFoundException: If the role with the specified slug does not exist.
        """
        try:
            return await self.get_one(
                slug=slug,
                load=load_only(self.model_type.id, self.model_type.slug),
            )
        except NotFoundError as exc:
            msg = "Role not found"
            raise NotFoundException(message=msg) from exc
