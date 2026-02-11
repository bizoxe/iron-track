"""User Account CRUD Endpoints.

Defines all user account CRUD operations, requiring superuser privileges.
"""

from typing import Annotated
from uuid import UUID

from advanced_alchemy.exceptions import (
    DuplicateKeyError,
    NotFoundError,
)
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import undefer

from app.db.models.user import User as UserModel
from app.domain.users import urls
from app.domain.users.auth import Authenticate
from app.domain.users.deps import (
    RoleServiceDep,
    UserServiceDep,
)
from app.domain.users.schemas import (
    User,
    UserAuth,
    UserCreate,
    UserUpdate,
)
from app.domain.users.utils import UserFilters
from app.lib.exceptions import (
    ConflictException,
    UserNotFound,
)
from app.lib.invalidate_cache import invalidate_user_cache
from app.lib.json_response import MsgSpecJSONResponse

users_router = APIRouter(
    tags=["User Accounts"],
)


@users_router.post(
    path=urls.USER_CREATE,
    operation_id="CreateUser",
    name="users:create",
    summary="Create a new user.",
    description="A user who can login and use the system.",
)
async def create_user(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    data: UserCreate,
) -> MsgSpecJSONResponse:
    """Create a new user in the system.

    Returns:
        ~app.domain.users.schemas.User: The newly created user data.

    Raises:
        ConflictException: If a user with the provided email already exists.
    """
    role_obj = await roles_service.get_default_role(
        default_role_slug=users_service.default_role,
    )
    try:
        db_obj = await users_service.create(data=data.model_dump(exclude_unset=True) | {"role_id": role_obj.id})
        user_dto = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user_dto, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = f"A user with the email '{data.email}' is already registered in the system"
        raise ConflictException(message=msg) from exc


@users_router.get(
    path=urls.USER_DETAIL,
    operation_id="GetUser",
    name="users:get",
    summary="Retrieve the details of a user.",
)
async def get_user(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    user_id: UUID,
) -> MsgSpecJSONResponse:
    """Retrieve a user by ID.

    Returns:
        ~app.domain.users.schemas.User: The detailed user data.

    Raises:
        UserNotFound: If the user with the given ID is not found.
    """
    try:
        db_obj = await users_service.get(user_id)
        user_dto = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user_dto)
    except NotFoundError as exc:
        raise UserNotFound from exc


@users_router.get(
    path=urls.USER_LIST,
    operation_id="ListUsers",
    name="users:list",
    summary="List of users.",
)
async def get_list_users(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    params: Annotated[UserFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of users.

    Returns:
        OffsetPagination[~app.domain.users.schemas.User]: Paginated list of users data.
    """
    filters = params.aa_technical_filters
    user_dto = await users_service.get_users_paginated_dto(filters)
    return MsgSpecJSONResponse(content=user_dto)


@users_router.patch(
    path=urls.USER_UPDATE,
    operation_id="UpdateUser",
    name="users:update",
    summary="Update user.",
)
async def update_user(
    super_user: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    data: UserUpdate,
    user_id: UUID,
) -> MsgSpecJSONResponse:
    """Update user details by ID.

    This action also invalidates the user's authentication cache in Redis.

    Returns:
        ~app.domain.users.schemas.User: The updated user data.

    Raises:
        UserNotFound: If the user is not found.
        ConflictException: If the new email provided is already in use by another user.
    """
    try:
        user_obj = await users_service.get(
            user_id,
            load=[undefer(UserModel.password)],
        )
        users_service.check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=super_user.id,
        )
        db_obj = await users_service.update(data=data, item_id=user_id)
        await invalidate_user_cache(
            user_id=db_obj.id,
        )
        user_dto = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user_dto)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            raise UserNotFound from exc
        msg = f"A user with the email '{data.email}' is already registered in the system"
        raise ConflictException(message=msg) from exc


@users_router.delete(
    path=urls.USER_DELETE,
    operation_id="DeleteUser",
    name="users:delete",
    summary="Delete user.",
)
async def delete_user(
    super_user: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    user_id: UUID,
) -> Response:
    """Delete a user from the system.

    This action also invalidates the user's authentication cache in Redis.

    Returns:
        Response: HTTP 204 No Content on successful deletion.

    Raises:
        UserNotFound: If the user is not found.
    """
    try:
        user_obj = await users_service.get(user_id)
        users_service.check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=super_user.id,
        )
        _ = await users_service.delete(item_id=user_id)
        await invalidate_user_cache(
            user_id=user_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        raise UserNotFound from exc
