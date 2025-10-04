import logging
from collections.abc import (
    Awaitable,
    Callable,
)
from typing import (
    Annotated,
    Any,
)

from advanced_alchemy.exceptions import NotFoundError
from fastapi import Depends
from jwt import PyJWTError

from src.domain.users.deps import UserService
from src.domain.users.schemas import UserAuth
from src.lib.exceptions import (
    PermissionDeniedException,
    UnauthorizedException,
    UserNotFound,
)
from src.lib.jwt_utils import decode_jwt
from src.lib.oauth2 import (
    access_token,
    refresh_token,
)

__all__ = ("Authenticate",)

log = logging.getLogger(__name__)


def get_payload_from_token(authentication_token: str) -> dict[str, Any] | None:
    try:
        payload = decode_jwt(token=authentication_token)
    except PyJWTError:
        log.exception(
            "An error occurred when decoding the token",
        )
        return None

    return payload


def get_user_by_token_sub(pyload: dict[str, Any] | None) -> str:
    if pyload is not None:
        user_id: str = pyload["sub"]
        return user_id
    raise UnauthorizedException(message="Invalid or expired token")


class Authenticate:
    @classmethod
    async def get_current_user_for_refresh(
        cls,
        token: Annotated[str, Depends(refresh_token)],
        users_service: UserService,
    ) -> UserAuth:
        token_payload = get_payload_from_token(authentication_token=token)
        user_id = get_user_by_token_sub(pyload=token_payload)
        try:
            db_obj = await users_service.get(user_id)
            if not db_obj.is_active:
                raise UnauthorizedException(message="Inactive user")
            return users_service.to_schema(db_obj, schema_type=UserAuth)
        except NotFoundError as exc:
            raise UserNotFound(user_id=user_id) from exc

    @classmethod
    async def get_current_user(
        cls,
        token: Annotated[str, Depends(access_token)],
        users_service: UserService,
    ) -> UserAuth:
        token_payload = get_payload_from_token(authentication_token=token)
        user_id = get_user_by_token_sub(pyload=token_payload)
        try:
            db_obj = await users_service.get(user_id)
            return users_service.to_schema(db_obj, schema_type=UserAuth)
        except NotFoundError as exc:
            raise UserNotFound(user_id=user_id) from exc

    @classmethod
    def get_current_active_user(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_user)],
        ) -> UserAuth:
            if not user_auth.is_active:
                raise UnauthorizedException(message="Inactive user")
            return user_auth

        return current_user

    @classmethod
    def superuser_required(cls) -> Callable[[UserAuth], Awaitable[UserAuth]]:
        async def current_user(
            user_auth: Annotated[UserAuth, Depends(cls.get_current_user)],
        ) -> UserAuth:
            if not user_auth.is_superuser:
                raise PermissionDeniedException(message="You do not have sufficient rights to access the resource")
            return user_auth

        return current_user
