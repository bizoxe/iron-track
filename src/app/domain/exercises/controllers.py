"""Exercise Management Endpoints.

Provides functionality for CRUD operations on exercises.
Distinguishes between user-defined custom exercises and system-wide defaults.

Creating, updating, and deleting system-default exercises requires superuser privileges.
"""

from typing import Annotated
from uuid import UUID

from advanced_alchemy.exceptions import DuplicateKeyError
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from app.config.constants import FITNESS_TRAINER_ROLE_SLUG
from app.domain.exercises import urls
from app.domain.exercises.deps import ExerciseServiceDep
from app.domain.exercises.schemas import (
    ExerciseCreate,
    ExerciseCreateSystem,
    ExerciseRead,
    ExerciseUpdate,
    ExerciseUpdateSystem,
)
from app.domain.exercises.utils import ExerciseFilters
from app.domain.users.auth import Authenticate
from app.domain.users.schemas import UserAuth
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)
from app.lib.json_response import MsgSpecJSONResponse

exercise_router = APIRouter(
    tags=["Exercises"],
)


@exercise_router.post(
    path=urls.USER_EXERCISE_CREATE,
    operation_id="CreateUserExercise",
    name="exercises:create",
    summary="Create a new user-defined exercise.",
)
async def create_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    exercise_create: ExerciseCreate,
) -> MsgSpecJSONResponse:
    """Create a new exercise for the current user.

    Returns:
        ExerciseRead: The created exercise data.

    Raises:
        ConflictException: If an exercise with the same name already exists for the user.
    """
    try:
        db_obj = await exercise_service.create(
            data=exercise_create.model_dump(exclude_unset=True, exclude_none=True) | {"created_by": user_auth.id},
        )
        exercise = exercise_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = (
            f"An exercise with the name '{exercise_create.name}'"
            " already exists in your account. Please choose a different name"
        )
        raise ConflictException(message=msg) from exc


@exercise_router.post(
    path=urls.SYSTEM_EXERCISE_CREATE,
    operation_id="CreateSystemExercise",
    name="exercises:create-system",
    summary="Create a new system-wide exercise.",
)
async def create_system_exercise(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercise_service: ExerciseServiceDep,
    exercise_create: ExerciseCreateSystem,
) -> MsgSpecJSONResponse:
    """Create a new system exercise.

    Requires superuser privileges.

    Returns:
        ExerciseRead: The created system exercise data.

    Raises:
        ConflictException: If a similar exercise already exists in the system.
    """
    try:
        db_obj = await exercise_service.create(
            data=exercise_create.model_dump(exclude_unset=True, exclude_none=True) | {"is_system_default": True},
        )
        exercise = exercise_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = (
            f"Exercise '{exercise_create.name}' cannot be created: a similar exercise "
            "(with matching normalized naming) already exists in the system"
        )
        raise ConflictException(message=msg) from exc


@exercise_router.get(
    path=urls.EXERCISE_DETAIL,
    operation_id="GetExercise",
    name="exercises:get",
    summary="Get details for a specific exercise.",
)
async def get_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    exercise_id: UUID,
) -> MsgSpecJSONResponse:
    """Get details for a specific exercise by its ID.

    Users can access their own exercises, system-default exercises,
    or exercises shared with them if they have the 'trainer' role.

    Returns:
        ExerciseRead: Detailed exercise data.

    Raises:
        NotFoundException: If the exercise is not found.
        PermissionDeniedException: If the user lacks access to the exercise.
    """
    db_obj = await exercise_service.get_one_or_none(id=exercise_id)
    if db_obj is None:
        msg = "Exercise not found"
        raise NotFoundException(message=msg)
    if not db_obj.is_system_default and (
        db_obj.created_by != user_auth.id and user_auth.role_slug != FITNESS_TRAINER_ROLE_SLUG
    ):
        msg = "You do not have permission to access this exercise"
        raise PermissionDeniedException(message=msg)
    exercise = exercise_service.to_schema(db_obj, schema_type=ExerciseRead)
    return MsgSpecJSONResponse(content=exercise)


@exercise_router.get(
    path=urls.EXERCISE_FIND,
    operation_id="FindExercise",
    name="exercises:find",
    summary="Find an exercise by name or slug.",
)
async def find_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    name: Annotated[str | None, Query(description="Search by exact name for user custom exercise.")] = None,
    slug: Annotated[str | None, Query(description="Search by unique slug for system exercise.")] = None,
) -> MsgSpecJSONResponse:
    """Find a user-defined or system exercise by name or slug.

    Returns:
        ExerciseRead: The found exercise data.

    Raises:
        NotFoundException: If no exercise matches the criteria.
    """
    exercise = await exercise_service.get_exercise_by_filter(
        user_id=user_auth.id,
        name=name,
        slug=slug,
    )
    return MsgSpecJSONResponse(content=exercise)


@exercise_router.get(
    path=urls.EXERCISE_LIST,
    operation_id="ListExercises",
    name="exercises:list",
    summary="List of exercises.",
)
async def get_list_exercises(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    params: Annotated[ExerciseFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a paginated list of exercises based on filters.

    Returns:
        OffsetPagination[ExerciseRead]: A paginated list of exercises.
    """
    exercises = await exercise_service.get_exercises_paginated_dto(params=params, user_id=user_auth.id)
    return MsgSpecJSONResponse(content=exercises)


@exercise_router.patch(
    path=urls.USER_EXERCISE_UPDATE,
    operation_id="UpdateUserExercise",
    name="exercises:update",
    summary="Update a user-defined exercise.",
)
async def update_user_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    exercise_update: ExerciseUpdate,
    exercise_id: UUID,
) -> MsgSpecJSONResponse:
    """Update details for a specific user-defined exercise.

    Returns:
        ExerciseRead: The updated exercise data.

    Raises:
        NotFoundException: If the exercise is not found.
        ConflictException: If the new name conflicts with an existing exercise.
    """
    try:
        db_obj = await exercise_service.update_exercise(
            exercise_id=exercise_id,
            data=exercise_update.model_dump(exclude_unset=True),
            extra_filters={"created_by": user_auth.id},
        )
        exercise = exercise_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise)
    except DuplicateKeyError as exc:
        msg = (
            f"An exercise with the name '{exercise_update.name}'"
            " already exists in your account. Please choose a different name"
        )
        raise ConflictException(message=msg) from exc


@exercise_router.patch(
    path=urls.SYSTEM_EXERCISE_UPDATE,
    operation_id="UpdateSystemExercise",
    name="exercises:update-system",
    summary="Update a system-wide exercise.",
)
async def update_system_exercise(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercise_service: ExerciseServiceDep,
    exercise_update: ExerciseUpdateSystem,
    exercise_id: UUID,
) -> MsgSpecJSONResponse:
    """Update details for a specific system exercise.

    Requires superuser privileges.

    Returns:
        ExerciseRead: The updated system exercise data.

    Raises:
        NotFoundException: If the system exercise is not found.
        ConflictException: If the new name conflicts with an existing system exercise.
    """
    try:
        db_obj = await exercise_service.update_exercise(
            exercise_id=exercise_id,
            data=exercise_update.model_dump(exclude_unset=True),
            extra_filters={"is_system_default": True},
        )
        exercise = exercise_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise)
    except DuplicateKeyError as exc:
        msg = (
            f"Exercise '{exercise_update.name}' cannot be created: a similar exercise "
            "(with matching normalized naming) already exists in the system"
        )
        raise ConflictException(message=msg) from exc


@exercise_router.delete(
    path=urls.EXERCISE_DELETE,
    operation_id="DeleteExercise",
    name="exercises:delete",
    summary="Delete a user-defined or system exercise.",
)
async def delete_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_service: ExerciseServiceDep,
    exercise_id: UUID,
) -> Response:
    """Delete a specific exercise by its ID.

    Users can delete their own exercises.
    Requires superuser privileges to delete system exercises.

    Returns:
        Response: 204 No Content on successful deletion.

    Raises:
        NotFoundException: If the exercise is not found.
        PermissionDeniedException: If the user lacks permission to delete the exercise.
    """
    await exercise_service.delete_exercise(exercise_id=exercise_id, user_auth=user_auth)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
