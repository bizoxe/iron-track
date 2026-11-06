"""Single entry point for user identity and account lifecycle.

Handles registration, login (JWT token issuance via cookies), token refreshing,
logout, and self-service profile actions (password update, account deletion).
Role-agnostic by design: superusers authenticate here as well.
"""

from time import time
from typing import Annotated

from advanced_alchemy.exceptions import DuplicateKeyError
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.config.base import get_settings
from app.config.constants import DEFAULT_USER_ROLE_SLUG
from app.domain.accounts import urls
from app.domain.accounts.auth import Authenticate
from app.domain.accounts.deps import (
    RoleServiceDep,
    UserServiceDep,
)
from app.domain.accounts.jwt_helpers import (
    add_token_to_blacklist,
    create_access_token,
    create_refresh_token,
)
from app.domain.accounts.schemas import (
    AccountRegister,
    PasswordUpdate,
    User,
    UserAuth,
)
from app.domain.accounts.utils import revoke_session
from app.lib.exceptions import ConflictException
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec
from app.lib.schema import ErrorInfo

settings = get_settings()

access_router = APIRouter(
    tags=["Accounts: Auth"],
)


@access_router.post(
    path=urls.ACCESS_REGISTER,
    operation_id="AccountRegister",
    name="access:register",
    summary="Register user",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=User, description="Created"),
        409: {
            "model": ErrorInfo,
        },
    },
)
async def register(
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    account_register: AccountRegister,
) -> MsgSpecJSONResponse:
    """Register new user."""
    role_obj = await roles_service.get_default_role(
        default_role_slug=DEFAULT_USER_ROLE_SLUG,
    )
    try:
        db_obj = await users_service.create(
            data=account_register.model_dump(exclude_unset=True) | {"role_id": role_obj.id},
            auto_refresh=False,
        )
        user = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "A user with this email already exists"
        raise ConflictException(message=msg) from exc


@access_router.post(
    path=urls.ACCESS_LOGIN,
    operation_id="AccountLogin",
    name="access:login",
    summary="Login",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        401: {
            "model": ErrorInfo,
        },
    },
)
async def login(
    users_service: UserServiceDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Response:
    """Login user.

    Issues access and refresh tokens. Stores tokens in cookies.
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
        max_age=settings.jwt.access_token_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.app.COOKIE_SECURE_VALUE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.jwt.refresh_token_max_age,
        httponly=True,
        samesite="strict",
        secure=settings.app.COOKIE_SECURE_VALUE,
    )

    return response


@access_router.get(
    path=urls.ACCESS_PROFILE,
    operation_id="AccountProfile",
    name="access:profile",
    summary="Get profile",
    responses={200: response_spec(schema=UserAuth)},
)
async def get_self_info(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
) -> MsgSpecJSONResponse:
    """Get user's account info."""
    return MsgSpecJSONResponse(content=user_auth)


@access_router.post(
    path=urls.ACCESS_REFRESH_TOKEN,
    operation_id="RefreshAccessToken",
    name="access:refresh",
    summary="Refresh tokens",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
    },
)
async def refresh_token(
    background_tasks: BackgroundTasks,
    auth_data: Annotated[tuple[UserAuth, str, float], Depends(Authenticate.get_current_user_with_refresh_context)],
) -> Response:
    """Issue new access and refresh tokens using the refresh token.

    Adds the expired refresh token to the blacklist as a background task.
    """
    user_auth, refresh_jti, refresh_exp = auth_data
    ttl = int(refresh_exp - time())
    if ttl > 0:
        background_tasks.add_task(
            add_token_to_blacklist,
            refresh_token_identifier=refresh_jti,
            ttl=ttl,
        )
    access_token = create_access_token(
        user_id=user_auth.id,
        email=user_auth.email,
    )
    refresh_token = create_refresh_token(user_id=user_auth.id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt.access_token_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.app.COOKIE_SECURE_VALUE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.jwt.refresh_token_max_age,
        httponly=True,
        samesite="strict",
        secure=settings.app.COOKIE_SECURE_VALUE,
    )

    return response


@access_router.patch(
    path=urls.ACCESS_UPDATE_PWD,
    operation_id="AccountUpdatePassword",
    name="access:update-password",
    summary="Update password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        401: {
            "model": ErrorInfo,
        },
    },
)
async def update_password(
    background_tasks: BackgroundTasks,
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    users_service: UserServiceDep,
    refresh_context: Annotated[tuple[str, float], Depends(Authenticate.get_refresh_jti)],
    pwd_data: PasswordUpdate,
) -> Response:
    """Update user password.

    Deletes access and refresh tokens from cookies, adds the refresh token to the blacklist,
    and invalidates user cache as a background task.
    """
    await users_service.update_password(
        data=pwd_data,
        user_id=user_auth.id,
    )
    refresh_jti, refresh_exp = refresh_context
    ttl = int(refresh_exp - time())
    if ttl > 0:
        background_tasks.add_task(
            func=revoke_session,
            refresh_jti=refresh_jti,
            ttl=ttl,
            user_id=user_auth.id,
        )
    response = Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@access_router.post(
    path=urls.ACCESS_LOGOUT,
    operation_id="AccountLogout",
    name="access:logout",
    summary="Logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
    },
)
async def logout(
    background_tasks: BackgroundTasks,
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    refresh_context: Annotated[tuple[str, float], Depends(Authenticate.get_refresh_jti)],
) -> Response:
    """Logout user.

    Deletes access and refresh tokens from cookies, adds the refresh token to the blacklist,
    and invalidates user cache as a background task.
    """
    refresh_jti, refresh_exp = refresh_context
    ttl = int(refresh_exp - time())
    if ttl > 0:
        background_tasks.add_task(
            func=revoke_session,
            refresh_jti=refresh_jti,
            ttl=ttl,
            user_id=user_auth.id,
        )
    response = Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@access_router.delete(
    path=urls.ACCESS_DELETE_ACCOUNT,
    operation_id="AccountDelete",
    name="access:delete-account",
    summary="Retire account",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        403: {"model": ErrorInfo},
    },
)
async def delete_account(
    background_tasks: BackgroundTasks,
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    users_service: UserServiceDep,
    refresh_context: Annotated[tuple[str, float], Depends(Authenticate.get_refresh_jti)],
) -> Response:
    """Retire the user's account.

    Deletes access and refresh tokens from cookies, adds the refresh token to the blacklist,
    and invalidates user cache as a background task.
    """
    await users_service.retire(user_id=user_auth.id)
    refresh_jti, refresh_exp = refresh_context
    ttl = int(refresh_exp - time())
    if ttl > 0:
        background_tasks.add_task(
            func=revoke_session,
            refresh_jti=refresh_jti,
            ttl=ttl,
            user_id=user_auth.id,
        )
    response = Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response
