"""User Account Endpoints.

Defines user-related operations, requiring superuser privileges.
Account deletion is intentionally absent: deletion belongs to the owners.
"""

from typing import Annotated
from uuid import UUID

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.config.constants import DEFAULT_USER_ROLE_SLUG
from app.domain.accounts import urls
from app.domain.accounts.auth import Authenticate
from app.domain.accounts.deps import RoleServiceDep, UserServiceDep
from app.domain.accounts.filters import UserExerciseFilters, UserFilters
from app.domain.accounts.schemas import (
    User,
    UserAuth,
    UserCreate,
    UserUpdate,
)
from app.domain.accounts.utils import invalidate_user_cache
from app.domain.exercises.deps import ExerciseServiceDep
from app.domain.exercises.schemas import ExerciseRead
from app.lib.exceptions import ConflictException, NotFoundException, UserNotFound
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec, response_spec_paginated
from app.lib.schema import ErrorInfo

users_router = APIRouter(
    tags=["Accounts"],
)


@users_router.post(
    path=urls.USER_CREATE,
    operation_id="CreateUser",
    name="users:create",
    summary="Create user",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=User, description="Created"),
        409: {
            "model": ErrorInfo,
        },
    },
)
async def create_user(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    roles_service: RoleServiceDep,
    data: UserCreate,
) -> MsgSpecJSONResponse:
    """Create a new user."""
    role_obj = await roles_service.get_default_role(
        default_role_slug=DEFAULT_USER_ROLE_SLUG,
    )
    try:
        db_obj = await users_service.create(
            data=data.model_dump(exclude_unset=True) | {"role_id": role_obj.id},
            auto_refresh=False,
        )
        user = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "A user with this email is already registered in the system"
        raise ConflictException(message=msg) from exc


@users_router.get(
    path=urls.USER_LIST,
    operation_id="ListUsers",
    name="users:list",
    summary="List of users",
    responses={200: response_spec_paginated(schema=User)},
)
async def get_list_users(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    params: Annotated[UserFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of users."""
    users = await users_service.get_users_paginated_dto(params)
    return MsgSpecJSONResponse(content=users)


@users_router.get(
    path=urls.USER_DETAIL,
    operation_id="GetUser",
    name="users:get",
    summary="Get user",
    responses={
        200: response_spec(schema=User),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_user(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    user_id: UUID,
) -> MsgSpecJSONResponse:
    """Get user by ID."""
    try:
        db_obj = await users_service.get(
            user_id,
            execution_options={"include_deleted": True},
        )
        user = users_service.to_schema(db_obj, schema_type=User)
        return MsgSpecJSONResponse(content=user)
    except NotFoundError as exc:
        raise UserNotFound from exc


@users_router.patch(
    path=urls.USER_UPDATE,
    operation_id="UpdateUser",
    name="users:update",
    summary="Update user",
    responses={
        200: response_spec(schema=User, description="Updated"),
        403: {
            "model": ErrorInfo,
        },
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def update_user(
    superuser: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    user_id: UUID,
    data: UserUpdate,
) -> MsgSpecJSONResponse:
    """Update user by ID.

    Security restrictions:

    * Self-modification is forbidden.
    * Modifying the primary system administrator account is forbidden.
    """
    db_obj = await users_service.update_user(
        data=data.model_dump(exclude_unset=True),
        user_id=user_id,
        superuser_id=superuser.id,
    )
    await invalidate_user_cache(user_id=db_obj.id)
    user = users_service.to_schema(db_obj, schema_type=User)
    return MsgSpecJSONResponse(content=user)


@users_router.get(
    path=urls.USER_EXERCISE_LIST,
    operation_id="ListUserExercises",
    name="users:list-user-exercises",
    summary="List of user's exercises",
    responses={
        200: response_spec_paginated(schema=ExerciseRead),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_list_user_exercises(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    users_service: UserServiceDep,
    exercises_service: ExerciseServiceDep,
    user_id: UUID,
    params: Annotated[UserExerciseFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of user's exercises."""
    exists = await users_service.exists(id=user_id)
    if not exists:
        raise UserNotFound
    filters = params.build_user_exercise_filters(user_id=user_id)
    results, total = await exercises_service.get_many_and_count(*filters)
    user_exercises = exercises_service.to_schema(
        data=results,
        total=total,
        filters=filters,
        schema_type=ExerciseRead,
    )
    return MsgSpecJSONResponse(content=user_exercises)


@users_router.get(
    path=urls.USER_EXERCISE_DETAIL,
    operation_id="GetUserExercise",
    name="users:get-user-exercise",
    summary="Get user's exercise",
    responses={
        200: response_spec(schema=ExerciseRead),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_user_exercise(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercises_service: ExerciseServiceDep,
    user_id: UUID,
    exercise_id: UUID,
) -> MsgSpecJSONResponse:
    """Get user's exercise by ID."""
    try:
        db_obj = await exercises_service.get_one(
            id=exercise_id,
            created_by=user_id,
        )
        user_exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=user_exercise)
    except NotFoundError as exc:
        msg = "Exercise not found"
        raise NotFoundException(message=msg) from exc
