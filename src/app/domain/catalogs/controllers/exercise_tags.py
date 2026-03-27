"""Exercise Tags Management Endpoints.

Provides functionality for CRUD operations on exercise tags.
Exercise tags are strictly system-wide identifiers used solely for classifying
and searching system-default exercises.

Users cannot associate tags with their custom exercises.
Creating, updating, and deleting tags requires superuser privileges.
Reading tag data is available to all authenticated users.
"""

from typing import Annotated

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

from app.domain.catalogs import urls
from app.domain.catalogs.deps import ExerciseTagDep
from app.domain.catalogs.schemas import (
    ExerciseTagCreate,
    ExerciseTagRead,
    ExerciseTagUpdate,
)
from app.domain.catalogs.utils import CatalogFilters
from app.domain.users.auth import Authenticate
from app.domain.users.schemas import UserAuth
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
)
from app.lib.json_response import MsgSpecJSONResponse

exercise_tags_router = APIRouter(
    tags=["Exercise Tags"],
)


@exercise_tags_router.post(
    path=urls.EXERCISE_TAG_CREATE,
    operation_id="CreateExerciseTag",
    name="exercise_tags:create",
    summary="Create exercise tag.",
)
async def create_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercise_tag_service: ExerciseTagDep,
    schema_data: ExerciseTagCreate,
) -> MsgSpecJSONResponse:
    """Create a new exercise tag entry.

    Requires superuser privileges.

    Returns:
        ExerciseTagRead: The created exercise tag data.

    Raises:
        ConflictException: If an exercise tag with the same name already exists.
    """
    try:
        db_obj = await exercise_tag_service.create(data=schema_data)
        exercise_tag = exercise_tag_service.to_schema(db_obj, schema_type=ExerciseTagRead)
        return MsgSpecJSONResponse(content=exercise_tag, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = f"An exercise tag with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@exercise_tags_router.get(
    path=urls.EXERCISE_TAG_LIST,
    operation_id="ListExerciseTags",
    name="exercise_tags:list",
    summary="List of exercise tags.",
)
async def get_list_exercise_tags(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_tag_service: ExerciseTagDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve all exercise tags with filtering and sorting.

    Returns:
        list[ExerciseTagRead]: A list of exercise tags items.
    """
    exercise_tags = await exercise_tag_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=exercise_tags)


@exercise_tags_router.get(
    path=urls.EXERCISE_TAG_DETAIL,
    operation_id="GetExerciseTag",
    name="exercise_tags:get",
    summary="Get exercise tag details.",
)
async def get_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    exercise_tag_service: ExerciseTagDep,
    tag_id: int,
) -> MsgSpecJSONResponse:
    """Get information about a specific exercise tag.

    Returns:
        ExerciseTagRead: Detailed exercise tag data.

    Raises:
        NotFoundException: If the exercise tag with the given ID does not exist.
    """
    try:
        db_obj = await exercise_tag_service.get(item_id=tag_id)
        exercise_tag = exercise_tag_service.to_schema(db_obj, schema_type=ExerciseTagRead)
        return MsgSpecJSONResponse(content=exercise_tag)
    except NotFoundError as exc:
        msg = f"Exercise tag with ID '{tag_id}' not found"
        raise NotFoundException(message=msg) from exc


@exercise_tags_router.patch(
    path=urls.EXERCISE_TAG_UPDATE,
    operation_id="UpdateExerciseTag",
    name="exercise_tags:update",
    summary="Update exercise tag.",
)
async def update_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercise_tag_service: ExerciseTagDep,
    schema_data: ExerciseTagUpdate,
    tag_id: int,
) -> MsgSpecJSONResponse:
    """Update information about a specific exercise tag.

    Requires superuser privileges.

    Returns:
        ExerciseTagRead: The updated exercise tag data.

    Raises:
        NotFoundException: If the exercise tag with the given ID does not exist.
        ConflictException: If an exercise tag with the same name already exists.
    """
    try:
        db_obj = await exercise_tag_service.update(
            item_id=tag_id,
            data=schema_data,
        )
        exercise_tag = exercise_tag_service.to_schema(db_obj, schema_type=ExerciseTagRead)
        return MsgSpecJSONResponse(content=exercise_tag)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = f"Exercise tag with ID '{tag_id}' not found"
            raise NotFoundException(message=msg) from exc
        msg = f"An exercise tag with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@exercise_tags_router.delete(
    path=urls.EXERCISE_TAG_DELETE,
    operation_id="DeleteExerciseTag",
    name="exercise_tags:delete",
    summary="Delete exercise tag.",
)
async def delete_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    exercise_tag_service: ExerciseTagDep,
    tag_id: int,
) -> Response:
    """Remove an exercise tag from the system.

    Requires superuser privileges.

    Returns:
        Response: 204 No Content on success.

    Raises:
        NotFoundException: If the exercise tag with the given ID does not exist.
    """
    try:
        await exercise_tag_service.delete(item_id=tag_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        msg = f"Exercise tag with ID '{tag_id}' not found"
        raise NotFoundException(message=msg) from exc
