from collections.abc import Awaitable, Callable
from typing import Annotated

from advanced_alchemy.exceptions import NotFoundError
from cashews import cache
from fastapi import Depends
from sqlalchemy.orm import joinedload, load_only

from app.config.base import get_settings
from app.config.constants import (
    DEFAULT_USER_ROLE_SLUG,
    FITNESS_TRAINER_ROLE_SLUG,
    SUPERUSER_ROLE_SLUG,
    USER_AUTH_CACHE_KEY_PREFIX,
)
from app.db.models.role import Role
from app.db.models.user import User
from app.domain.accounts.deps import UserServiceDep
from app.domain.accounts.jwt_helpers import (
    TokenPayloadBase,
    get_access_token_payload,
    get_refresh_token_payload,
    is_token_in_blacklist,
)
from app.domain.accounts.schemas import UserAuth
from app.lib.auth import access_token, refresh_token
from app.lib.exceptions import (
    PermissionDeniedException,
    UnauthorizedException,
)


class Authenticate:
    """FastAPI auth dependencies and factories."""

    @classmethod
    @cache(
        ttl=get_settings().app.user_auth_cache_ttl,
        key=USER_AUTH_CACHE_KEY_PREFIX + ":{token_payload.sub}",
    )
    async def _get_user_from_payload(
        cls,
        users_service: UserServiceDep,
        token_payload: TokenPayloadBase,
    ) -> UserAuth:
        """Load UserAuth schema from the database or cache.

        Args:
            users_service (UserService): Dependency for user service operations.
            token_payload (TokenPayloadBase): The token data.

        Returns:
            UserAuth: The authenticated user.

        Raises:
            UnauthorizedException: If the user is not found.
        """
        user_id = token_payload.sub
        try:
            db_obj = await users_service.get(
                item_id=user_id,
                load=[
                    load_only(
                        User.id,
                        User.name,
                        User.email,
                        User.is_active,
                        User.is_superuser,
                    ),
                    joinedload(User.role, innerjoin=True).load_only(Role.slug),
                ],
            )
            return users_service.to_schema(db_obj, schema_type=UserAuth)
        except NotFoundError as exc:
            msg = "Invalid authentication credentials"
            raise UnauthorizedException(message=msg) from exc

    @classmethod
    async def get_current_user_with_refresh_context(
        cls,
        token: Annotated[str, Depends(refresh_token)],
        users_service: UserServiceDep,
    ) -> tuple[UserAuth, str, float]:
        """Authenticate the user via refresh token and check blacklisting.

        Args:
            token (str): The refresh token extracted from the cookie.
            users_service (UserService): Dependency for user service operations.

        Returns:
            tuple[UserAuth, str, float]: The authenticated user along with
                the refresh JTI and expiration timestamp.

        Raises:
            UnauthorizedException: If the token is invalid, blacklisted, or the user is inactive.
        """
        token_payload = get_refresh_token_payload(token=token)
        refresh_jti = token_payload.jti
        token_exists = await is_token_in_blacklist(
            refresh_token_identifier=refresh_jti,
        )
        if token_exists:
            msg = "Invalid credentials"
            raise UnauthorizedException(message=msg)
        user_auth = await cls._get_user_from_payload(
            token_payload=token_payload,
            users_service=users_service,
        )
        if not user_auth.is_active:
            msg = "Invalid credentials or account is unavailable"
            raise UnauthorizedException(message=msg)

        user_auth._refresh_jti = refresh_jti  # noqa: SLF001
        user_auth._refresh_exp = token_payload.exp  # noqa: SLF001
        return user_auth, refresh_jti, token_payload.exp

    @classmethod
    async def get_current_user(
        cls,
        token: Annotated[str, Depends(access_token)],
        users_service: UserServiceDep,
    ) -> UserAuth:
        """Authenticate the user via the access token.

        Args:
            token (str): The access token extracted from the cookie.
            users_service (UserService): Dependency for user service operations.

        Returns:
            UserAuth: The authenticated user.
        """
        token_payload = await get_access_token_payload(token=token)
        return await cls._get_user_from_payload(
            token_payload=token_payload,
            users_service=users_service,
        )

    @classmethod
    def get_current_active_user(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory to ensure the user is active.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            UnauthorizedException: If the user is found but not active.
        """

        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_user)],
        ) -> UserAuth:
            if not user_auth.is_active:
                raise UnauthorizedException(message="Invalid credentials or account is unavailable")
            return user_auth

        return current_user

    @classmethod
    def application_access_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory for user-area endpoints.

        Requires an active user with a user-area role: application-access or
        fitness-trainer. Superusers are deliberately excluded.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            PermissionDeniedException: If the user lacks a user-area role.
        """

        async def current_active_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_active_user())],
        ) -> UserAuth:
            if user_auth.role_slug not in (DEFAULT_USER_ROLE_SLUG, FITNESS_TRAINER_ROLE_SLUG):
                raise PermissionDeniedException(message="Access denied")
            return user_auth

        return current_active_user

    @classmethod
    def superuser_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory requiring the Superuser role.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            PermissionDeniedException: If the user does not have the required role.
        """

        async def current_active_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_active_user())],
        ) -> UserAuth:
            if user_auth.role_slug != SUPERUSER_ROLE_SLUG:
                raise PermissionDeniedException(message="Access restricted to superusers")
            return user_auth

        return current_active_user

    @classmethod
    def trainer_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory requiring the Fitness Trainer role.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            PermissionDeniedException: If the user does not have the required role.
        """

        async def current_active_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_active_user())],
        ) -> UserAuth:
            if user_auth.role_slug != FITNESS_TRAINER_ROLE_SLUG:
                raise PermissionDeniedException(message="Access restricted to fitness trainers")
            return user_auth

        return current_active_user

    @classmethod
    def get_refresh_jti(
        cls,
        token: Annotated[str, Depends(refresh_token)],
    ) -> tuple[str, float]:
        """Extract the JWT ID (jti) and expiration (exp) from a refresh token.

        Args:
            token (str): The refresh token string from the cookie.

        Returns:
            tuple[str, float]: The JTI claim and expiration timestamp.
        """
        token_payload = get_refresh_token_payload(token=token)

        return token_payload.jti, token_payload.exp
