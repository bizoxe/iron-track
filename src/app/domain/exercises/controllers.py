"""Exercise Management Endpoints.

Provides functionality for CRUD operations on exercises.
Distinguishes between system exercises and user-defined custom exercises.

Creating or updating system exercises requires superuser privileges.
System exercises cannot be deleted.
This module does not provide superusers with access to user exercises.
"""

from typing import Annotated, Literal
from uuid import UUID

from advanced_alchemy.exceptions import DuplicateKeyError
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from app.domain.accounts.auth import Authenticate
from app.domain.accounts.schemas import UserAuth
from app.domain.exercises import urls
from app.domain.exercises.deps import ExerciseServiceDep
from app.domain.exercises.filters import ExerciseFilters
from app.domain.exercises.schemas import (
    ExerciseCreate,
    ExerciseCreateSystem,
    ExerciseRead,
    ExerciseScope,
    ExerciseUpdate,
    ExerciseUpdateSystem,
)
from app.domain.exercises.utils import can_access_exercise
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec, response_spec_paginated
from app.lib.schema import ErrorInfo

exercises_router = APIRouter(
    tags=["Exercises"],
)


@exercises_router.post(
    path=urls.EXERCISE_CREATE,
    operation_id="CreateExercise",
    name="exercises:create",
    summary="Create custom exercise",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=ExerciseRead, description="Created"),
        409: {"model": ErrorInfo},
    },
)
async def create_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.application_access_required())],
    exercises_service: ExerciseServiceDep,
    data: ExerciseCreate,
) -> MsgSpecJSONResponse:
    """Create user-defined exercise."""
    try:
        db_obj = await exercises_service.create(
            data=data.model_dump(exclude_unset=True) | {"created_by": user_auth.id},
        )
        exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "An exercise with this or a similar name already exists"
        raise ConflictException(message=msg) from exc


@exercises_router.post(
    path=urls.SYSTEM_EXERCISE_CREATE,
    operation_id="CreateSystemExercise",
    name="exercises:create-system",
    summary="Create system exercise",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=ExerciseRead, description="Created"),
        409: {"model": ErrorInfo},
    },
)
async def create_system_exercise(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercises_service: ExerciseServiceDep,
    data: ExerciseCreateSystem,
) -> MsgSpecJSONResponse:
    """Create system exercise.

    Requires superuser privileges.
    """
    try:
        db_obj = await exercises_service.create(
            data=data.model_dump(exclude_unset=True) | {"is_system_default": True},
        )
        exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "An exercise with this or a similar name already exists"
        raise ConflictException(message=msg) from exc


@exercises_router.get(
    path=urls.EXERCISE_LIST,
    operation_id="ListExercises",
    name="exercises:list",
    summary="List of exercises",
    responses={200: response_spec_paginated(schema=ExerciseRead)},
)
async def get_list_exercises(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercises_service: ExerciseServiceDep,
    params: Annotated[ExerciseFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of exercises.

    Visibility:

    * System exercises are visible to all users.
    * User exercises are visible only to their owners.
    """
    exercises = await exercises_service.get_exercises_paginated_dto(params=params, user_id=user_auth.id)
    return MsgSpecJSONResponse(content=exercises)


@exercises_router.get(
    path=urls.EXERCISE_LOOKUP,
    operation_id="LookupExercise",
    name="exercises:lookup",
    summary="Lookup exercise by name",
    responses={
        200: response_spec(schema=ExerciseRead),
        404: {"model": ErrorInfo},
    },
)
async def lookup_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercises_service: ExerciseServiceDep,
    scope: Annotated[
        Literal[ExerciseScope.USER, ExerciseScope.SYSTEM],
        Query(description="Data ownership scope (user or system)."),
    ],
    name: Annotated[str, Query(min_length=3, max_length=100, description="Exact exercise name.")],
) -> MsgSpecJSONResponse:
    """Look up an exercise by name.

    Visibility:

    * System exercises are visible to all users.
    * User exercises are visible only to their owners.
    """
    db_obj = await exercises_service.get_by_name(
        user_id=user_auth.id,
        scope=scope,
        name=name,
    )
    exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
    return MsgSpecJSONResponse(content=exercise)


@exercises_router.get(
    path=urls.EXERCISE_DETAIL,
    operation_id="GetExercise",
    name="exercises:get",
    summary="Get exercise",
    responses={
        200: response_spec(schema=ExerciseRead),
        403: {"model": ErrorInfo},
        404: {"model": ErrorInfo},
    },
)
async def get_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercises_service: ExerciseServiceDep,
    exercise_id: UUID,
) -> MsgSpecJSONResponse:
    """Get exercise by ID.

    Security restrictions:

    * System exercises are accessible to all users.
    * User exercises are accessible only to their owners.
    """
    db_obj = await exercises_service.get_one_or_none(id=exercise_id)
    if db_obj is None:
        raise NotFoundException(message="Exercise not found")
    if not can_access_exercise(
        exercise=db_obj,
        user=user_auth,
    ):
        msg = "You do not have permission to access this exercise"
        raise PermissionDeniedException(message=msg)
    exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
    return MsgSpecJSONResponse(content=exercise)


@exercises_router.patch(
    path=urls.EXERCISE_UPDATE,
    operation_id="UpdateExercise",
    name="exercises:update",
    summary="Update custom exercise",
    responses={
        200: response_spec(schema=ExerciseRead, description="Updated"),
        404: {"model": ErrorInfo},
        409: {"model": ErrorInfo},
    },
)
async def update_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.application_access_required())],
    exercises_service: ExerciseServiceDep,
    exercise_id: UUID,
    data: ExerciseUpdate,
) -> MsgSpecJSONResponse:
    """Update user-defined exercise."""
    if not await exercises_service.exercise_exists(
        exercise_id=exercise_id,
        created_by=user_auth.id,
    ):
        raise NotFoundException(message="Exercise not found")
    try:
        db_obj = await exercises_service.update(
            item_id=exercise_id,
            data=data.model_dump(exclude_unset=True),
        )
        exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise)
    except DuplicateKeyError as exc:
        msg = "An exercise with this or a similar name already exists"
        raise ConflictException(message=msg) from exc


@exercises_router.patch(
    path=urls.SYSTEM_EXERCISE_UPDATE,
    operation_id="UpdateSystemExercise",
    name="exercises:update-system",
    summary="Update system exercise",
    responses={
        200: response_spec(schema=ExerciseRead, description="Updated"),
        404: {"model": ErrorInfo},
        409: {"model": ErrorInfo},
    },
)
async def update_system_exercise(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercises_service: ExerciseServiceDep,
    exercise_id: UUID,
    data: ExerciseUpdateSystem,
) -> MsgSpecJSONResponse:
    """Update system exercise.

    Requires superuser privileges.
    """
    if not await exercises_service.exercise_exists(
        exercise_id=exercise_id,
        created_by=None,
    ):
        raise NotFoundException(message="Exercise not found")
    try:
        db_obj = await exercises_service.update(
            item_id=exercise_id,
            data=data.model_dump(exclude_unset=True),
        )
        exercise = exercises_service.to_schema(db_obj, schema_type=ExerciseRead)
        return MsgSpecJSONResponse(content=exercise)
    except DuplicateKeyError as exc:
        msg = "An exercise with this or a similar name already exists"
        raise ConflictException(message=msg) from exc


@exercises_router.delete(
    path=urls.EXERCISE_DELETE,
    operation_id="DeleteExercise",
    name="exercises:delete",
    summary="Delete exercise",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        403: {
            "model": ErrorInfo,
        },
        404: {
            "model": ErrorInfo,
        },
    },
)
async def delete_exercise(
    user_auth: Annotated[UserAuth, Depends(Authenticate.application_access_required())],
    exercises_service: ExerciseServiceDep,
    exercise_id: UUID,
) -> Response:
    """Delete exercise by ID.

    Security restrictions:

    * Users can delete only their own exercises.
    * System exercises cannot be deleted.
    """
    await exercises_service.delete_exercise(exercise_id=exercise_id, user_auth=user_auth)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
