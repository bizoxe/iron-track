"""User Account CRUD Endpoints.

Defines all user account CRUD operations, requiring superuser privileges.
"""

from typing import Annotated
from uuid import UUID

from advanced_alchemy.exceptions import (
    DuplicateKeyError,
    NotFoundError,
)
from advanced_alchemy.extensions.fastapi import filters as alchemy_filters
from advanced_alchemy.service import OffsetPagination
from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from fastapi_cache.decorator import cache

from app.config.app_settings import alchemy
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
from app.lib.cache_key_builders import query_params_key_builder
from app.lib.coders import MsgPackCoder
from app.lib.deps import RedisClientDep
from app.lib.exceptions import (
    ConflictException,
    UserNotFound,
)
from app.lib.invalidate_cache import invalidate_user_cache
from app.lib.json_response import MsgSpecJSONResponse

users_router = APIRouter(
    tags=["User Accounts"],
    default_response_class=MsgSpecJSONResponse,
)


@users_router.post(
    path=urls.USER_CREATE,
    operation_id="CreateUser",
    status_code=status.HTTP_201_CREATED,
    name="users:create",
    summary="Create a new user.",
    description="A user who can login and use the system.",
)
async def create_user(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    data: UserCreate,
) -> User:
    """Create a new user in the system."""
    role_obj = await roles_service.get_default_role(
        default_role_slug=users_service.default_role,
    )
    try:
        db_obj = await users_service.create(data=data.model_dump() | {"role_id": role_obj.id})
        return users_service.to_schema(db_obj, schema_type=User)
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
) -> User:
    """Retrieve a user by ID."""
    try:
        db_obj = await users_service.get(user_id)
        return users_service.to_schema(db_obj, schema_type=User)
    except NotFoundError as exc:
        raise UserNotFound from exc


@users_router.get(
    path=urls.USER_LIST,
    operation_id="ListUsers",
    name="users:list",
    summary="List of users.",
)
@cache(
    expire=60,
    coder=MsgPackCoder,
    key_builder=query_params_key_builder,
)
async def get_list_users(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    filters: Annotated[
        list[alchemy_filters.FilterTypes],
        Depends(
            alchemy.provide_filters(
                {
                    "id_filter": UUID,
                    "pagination_type": "limit_offset",
                    "search": "name,email",
                    "pagination_size": 20,
                    "created_at": True,
                    "updated_at": True,
                    "sort_field": "name",
                    "sort_order": "asc",
                }
            )
        ),
    ],
) -> OffsetPagination[User]:
    """Retrieve a list of users."""
    results, total = await users_service.list_and_count(*filters)

    return users_service.to_schema(data=results, total=total, schema_type=User, filters=filters)


@users_router.patch(
    path=urls.USER_UPDATE,
    operation_id="UpdateUser",
    name="users:update",
    summary="Update user.",
)
async def update_user(
    super_user: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    redis_client: RedisClientDep,
    data: UserUpdate,
    user_id: UUID,
) -> User:
    """Update user by ID."""
    try:
        user_obj = await users_service.get(user_id)
        users_service.check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=super_user.id,
        )
        db_obj = await users_service.update(data=data, item_id=user_id)
        await invalidate_user_cache(
            user_id=db_obj.id,
            redis_client=redis_client,
        )
        return users_service.to_schema(db_obj, schema_type=User)
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
    redis_client: RedisClientDep,
    user_id: UUID,
) -> Response:
    """Delete a user from the system."""
    try:
        user_obj = await users_service.get(user_id)
        users_service.check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=super_user.id,
        )
        _ = await users_service.delete(item_id=user_id)
        await invalidate_user_cache(
            user_id=user_id,
            redis_client=redis_client,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        raise UserNotFound from exc
