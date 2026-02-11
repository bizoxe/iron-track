from collections.abc import (
    Awaitable,
    Callable,
)
from typing import (
    Annotated,
    Any,
)

from advanced_alchemy.exceptions import NotFoundError
from cashews import cache
from fastapi import Depends
from joserfc.errors import JoseError
from joserfc.jwt import JWTClaimsRegistry
from sqlalchemy.orm import (
    load_only,
    selectinload,
)
from structlog import get_logger

from app.config.constants import (
    FITNESS_TRAINER_ROLE_SLUG,
    USER_AUTH_CACHE_TTL,
)
from app.db.models.role import Role
from app.db.models.user import User
from app.domain.users.deps import UserServiceDep
from app.domain.users.jwt_helpers import is_token_in_blacklist
from app.domain.users.schemas import UserAuth
from app.lib.auth import (
    access_token,
    refresh_token,
)
from app.lib.exceptions import (
    PermissionDeniedException,
    UnauthorizedException,
)
from app.lib.jwt_utils import decode_jwt

__all__ = ("Authenticate",)

log = get_logger()

claims_registry = JWTClaimsRegistry(
    exp={"essential": True},
    iat={"essential": True},
)


def get_payload_from_token(authentication_token: str) -> dict[str, Any]:
    """Decode a JWT token and return its payload.

    Args:
        authentication_token (str): The raw JWT string.

    Returns:
        dict: The decoded JWT payload as a dictionary.

    Raises:
        UnauthorizedException: If the token is invalid, malformed, or expired (HTTP 401).
    """
    try:
        claims = decode_jwt(token=authentication_token).claims
        claims_registry.validate(claims=claims)
    except JoseError as exc:
        log.warning(
            "JWT decode failed",
            error_type=type(exc).__name__,
            error_detail=str(exc),
        )
        msg = "Invalid or expired token"
        raise UnauthorizedException(message=msg) from exc
    else:
        return claims


class Authenticate:
    """Provides FastAPI dependency factories for authentication and authorization."""

    @classmethod
    @cache(
        ttl=USER_AUTH_CACHE_TTL,
        key="user_auth:{token_payload[sub]}",
    )
    async def _get_user_from_payload(
        cls,
        token_payload: dict[str, Any],
        users_service: UserServiceDep,
    ) -> UserAuth:
        """Load UserAuth schema from the database using the JWT 'sub' claim.

        The result of this function is aggressively cached to reduce database load.

        Args:
            token_payload (dict): The decoded JWT payload.
            users_service (UserService): Dependency for user service operations.

        Returns:
            UserAuth: The authenticated user.

        Raises:
            UnauthorizedException: If the user is not found (HTTP 401).
        """
        user_id = token_payload["sub"]
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
                    selectinload(User.role).load_only(Role.slug),
                ],
            )
            return users_service.to_schema(db_obj, schema_type=UserAuth)
        except NotFoundError as exc:
            msg = "Invalid authentication credentials"
            raise UnauthorizedException(message=msg) from exc

    @classmethod
    async def get_current_user_for_refresh(
        cls,
        token: Annotated[str, Depends(refresh_token)],
        users_service: UserServiceDep,
    ) -> UserAuth:
        """Authenticate the user using the refresh token.

        Performs critical security checks including token blacklisting. This dependency
        is used exclusively by the token refresh endpoint.

        Args:
            token (str): The refresh token extracted from the cookie.
            users_service (UserService): Dependency for user service operations.

        Returns:
            UserAuth: The authenticated user with JTI attached.

        Raises:
            UnauthorizedException: If the token is invalid, blacklisted, or the user is inactive (HTTP 401).
        """
        token_payload = get_payload_from_token(authentication_token=token)
        refresh_jti = token_payload["jti"]
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
        return user_auth

    @classmethod
    async def get_current_user(
        cls,
        token: Annotated[str, Depends(access_token)],
        users_service: UserServiceDep,
    ) -> UserAuth:
        """Authenticate the user using the access token.

        Args:
            token (str): The access token extracted from the cookie.
            users_service (UserService): Dependency for user service operations.

        Returns:
            UserAuth: The authenticated user.
        """
        token_payload = get_payload_from_token(authentication_token=token)
        return await cls._get_user_from_payload(
            token_payload=token_payload,
            users_service=users_service,
        )

    @classmethod
    def get_current_active_user(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory to ensure the user is active.

        It chains with `get_current_user` to perform both authentication and
        basic authorization (account status check).

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            UnauthorizedException: If the user is found but not active (HTTP 401).
        """

        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_user)],
        ) -> UserAuth:
            if not user_auth.is_active:
                raise UnauthorizedException(message="Invalid credentials or account is unavailable")
            return user_auth

        return current_user

    @classmethod
    def superuser_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory requiring superuser privileges.

        It chains with `get_current_active_user` and performs the final authorization check.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            PermissionDeniedException: If the user is not a superuser (HTTP 403).
        """

        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_active_user())],
        ) -> UserAuth:
            if not user_auth.is_superuser:
                msg = "Access denied: Superuser privileges required"
                raise PermissionDeniedException(message=msg)
            return user_auth

        return current_user

    @classmethod
    def trainer_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        """Dependency factory requiring the Fitness Trainer role.

        It chains with `get_current_active_user` and performs the final role check.

        Returns:
            Callable: A FastAPI dependency function.

        Raises:
            PermissionDeniedException: If the user does not have the required role (HTTP 403).
        """

        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_active_user())],
        ) -> UserAuth:
            if user_auth.role_slug == FITNESS_TRAINER_ROLE_SLUG:
                return user_auth
            msg = "Access restricted to fitness trainers"
            raise PermissionDeniedException(message=msg)

        return current_user

    @classmethod
    def get_refresh_jti(
        cls,
        token: Annotated[str, Depends(refresh_token)],
    ) -> str:
        """Extract the JWT ID (jti) claim from a refresh token.

        This method is primarily used to retrieve the JTI for blacklisting
        during the token refresh process.

        Args:
            token (str): The refresh token string from the cookie.

        Returns:
            str: The JTI claim.
        """
        token_payload = get_payload_from_token(authentication_token=token)
        token_identifier: str = token_payload["jti"]

        return token_identifier
