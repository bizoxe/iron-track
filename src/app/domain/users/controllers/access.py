"""User Access and Authentication Endpoints.

Handles user registration, login (JWT token issuance via cookies), token refreshing, logout,
and user-specific profile actions.
"""

from typing import Annotated

from advanced_alchemy.exceptions import DuplicateKeyError
from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from starlette.background import (
    BackgroundTask,
    BackgroundTasks,
)

from app.config import constants
from app.config.base import get_settings
from app.domain.users import urls
from app.domain.users.auth import Authenticate
from app.domain.users.deps import (
    RoleServiceDep,
    UserServiceDep,
)
from app.domain.users.jwt_helpers import (
    add_token_to_blacklist,
    create_access_token,
    create_refresh_token,
)
from app.domain.users.schemas import (
    AccountRegister,
    PasswordUpdate,
    User,
    UserAuth,
)
from app.domain.users.utils import perform_logout_cleanup
from app.lib.deps import RedisClientDep
from app.lib.exceptions import ConflictException
from app.lib.invalidate_cache import invalidate_user_cache
from app.lib.json_response import MsgSpecJSONResponse

access_router = APIRouter(
    tags=["Access"],
    default_response_class=MsgSpecJSONResponse,
)

settings = get_settings()


@access_router.post(
    path=urls.ACCOUNT_REGISTER,
    status_code=status.HTTP_201_CREATED,
    operation_id="AccountRegister",
    name="access:signup",
    summary="Register a new user.",
)
async def signup(
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    account_register: AccountRegister,
) -> User:
    """User Signup.

    Returns:
        ~app.domain.users.schemas.User: The newly registered user.

    Raises:
        ConflictException: If a user with this email already exists.
    """
    role_obj = await roles_service.get_default_role(
        default_role_slug=users_service.default_role,
    )
    try:
        user = await users_service.create(
            data=account_register.model_dump() | {"role_id": role_obj.id},
        )
        return users_service.to_schema(user, schema_type=User)
    except DuplicateKeyError as exc:
        msg = "A user with this email already exists"
        raise ConflictException(message=msg) from exc


@access_router.post(
    path=urls.ACCOUNT_LOGIN,
    operation_id="AccountLogin",
    status_code=status.HTTP_204_NO_CONTENT,
    name="access:login",
    summary="Account login, issue access and refresh tokens.",
)
async def login_for_access_token(
    users_service: UserServiceDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Response:
    """Issue access and refresh tokens. Store tokens in cookies.

    Returns:
        Response: HTTP 204 No Content response with access and refresh tokens set as cookies.

    Raises:
        UnauthorizedException: If authentication fails (handled by dependencies).
    """
    user = await users_service.authenticate(
        username=form_data.username,
        password=form_data.password,
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=constants.ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=constants.COOKIE_SECURE_VALUE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=constants.REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        samesite="strict",
        secure=constants.COOKIE_SECURE_VALUE,
    )

    return response


@access_router.post(
    path=urls.ACCOUNT_REFRESH_TOKEN,
    operation_id="RefreshAccessToken",
    status_code=status.HTTP_204_NO_CONTENT,
    name="access:refresh",
    summary="Issue a new access token using the refresh token.",
)
async def user_auth_refresh_token(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_user_for_refresh)],
    redis_client: RedisClientDep,
) -> Response:
    """Get the user by the refresh token and issue a new access token.

    The expired refresh token is added to the blacklist as a background task.

    Returns:
        Response: HTTP 204 No Content response with new access and refresh tokens.
    """
    access_token = create_access_token(
        user_id=user_auth.id,
        email=user_auth.email,
    )
    refresh_token = create_refresh_token(user_id=user_auth.id)
    background_task = BackgroundTask(
        func=add_token_to_blacklist,
        refresh_token_identifier=user_auth._refresh_jti,  # type: ignore[arg-type]  # noqa: SLF001
        redis_client=redis_client,
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT, background=background_task)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=constants.ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=constants.COOKIE_SECURE_VALUE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=constants.REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        samesite="strict",
        secure=constants.COOKIE_SECURE_VALUE,
    )

    return response


@access_router.post(
    path=urls.ACCOUNT_LOGOUT,
    operation_id="AccountLogout",
    name="access:logout",
    summary="Log out, delete tokens from cookie.",
)
async def logout(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    refresh_jti: Annotated[str, Depends(Authenticate.get_refresh_jti)],
    redis_client: RedisClientDep,
) -> Response:
    """User Logout.

    Deletes access and refresh tokens from cookies and invalidates the refresh token JTI
    in Redis as a background task.

    Returns:
        Response: HTTP 204 No Content response.
    """
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        func=perform_logout_cleanup,
        refresh_jti=refresh_jti,
        user_id=user_auth.id,
        redis_client=redis_client,
    )
    response = Response(
        status_code=status.HTTP_204_NO_CONTENT,
        background=background_tasks,
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@access_router.patch(
    path=urls.ACCOUNT_PWD_UPDATE,
    operation_id="AccountUpdatePwd",
    name="access:update-pwd",
    summary="Update your user password.",
)
async def update_password(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    users_service: UserServiceDep,
    redis_client: RedisClientDep,
    pwd_data: PasswordUpdate,
) -> Response:
    """Update user password.

    This action also invalidates the user's authentication cache in Redis.

    Returns:
        Response: HTTP 204 No Content response.
    """
    await users_service.update_password(
        data=pwd_data,
        user_id=user_auth.id,
    )
    await invalidate_user_cache(
        user_id=user_auth.id,
        redis_client=redis_client,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@access_router.get(
    path=urls.ACCOUNT_PROFILE,
    operation_id="AccountProfile",
    name="access:profile",
    summary="Get information about yourself by the user.",
)
async def user_auth_get_self_info(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
) -> UserAuth:
    """Get self account info.

    Returns:
        UserAuth: The authenticated user's details.
    """
    return user_auth
