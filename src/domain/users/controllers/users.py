"""User Account CRUD Endpoints.

Defines all user account CRUD operations, requiring superuser privileges.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
)
from uuid import UUID

from advanced_alchemy.exceptions import (
    DuplicateKeyError,
    NotFoundError,
)
from advanced_alchemy.filters import FilterTypes  # noqa: TC002
from advanced_alchemy.service import OffsetPagination
from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from fastapi_cache.decorator import cache

from src.config.app_settings import alchemy
from src.domain.users import urls
from src.domain.users.auth import Authenticate
from src.domain.users.deps import (
    RoleServiceDep,  # noqa: TC001
    UserServiceDep,  # noqa: TC001
)
from src.domain.users.schemas import (
    User,
    UserAuth,
    UserCreate,
    UserUpdate,
)
from src.lib.cache_key_builders import query_params_key_builder
from src.lib.coders import MsgPackCoder
from src.lib.exceptions import (
    ConflictException,
    UserNotFound,
)
from src.lib.invalidate_cache import invalidate_user_cache
from src.lib.json_response import MsgSpecJSONResponse

if TYPE_CHECKING:
    from db.models import User as UserModel

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
    response_model=OffsetPagination[User],
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
        list[FilterTypes],
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
) -> OffsetPagination[UserModel]:
    """Retrieve a list of users."""
    results, count = await users_service.list_and_count(*filters)

    return users_service.to_schema(results, count, filters=filters, schema_type=User)


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
) -> User:
    """Update user by ID."""
    try:
        user_obj = await users_service.get(user_id)
        users_service.check_critical_action_forbidden(
            target_user=user_obj,
            calling_superuser_id=super_user.id,
        )
        db_obj = await users_service.update(data=data, item_id=user_id)
        await invalidate_user_cache(user_id=db_obj.id)
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
        await invalidate_user_cache(user_id=user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        raise UserNotFound from exc
