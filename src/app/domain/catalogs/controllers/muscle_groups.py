"""Muscle Groups Management Endpoints.

Provides functionality for CRUD operations on muscle groups.

Creating, updating, and deleting muscle group entries requires superuser privileges.
Reading muscle group data is available to all authenticated users.
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
from app.domain.catalogs.deps import MuscleGroupDep
from app.domain.catalogs.schemas import (
    MuscleGroupCreate,
    MuscleGroupRead,
    MuscleGroupUpdate,
)
from app.domain.catalogs.utils import CatalogFilters
from app.domain.users.auth import Authenticate
from app.domain.users.schemas import UserAuth
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
)
from app.lib.json_response import MsgSpecJSONResponse

muscle_router = APIRouter(
    tags=["Muscle Groups"],
)


@muscle_router.post(
    path=urls.MUSCLE_GROUP_CREATE,
    operation_id="CreateMuscleGroup",
    name="muscles:create",
    summary="Create a new muscle group.",
)
async def create_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_service: MuscleGroupDep,
    schema_data: MuscleGroupCreate,
) -> MsgSpecJSONResponse:
    """Create a new muscle group entry.

    Requires superuser privileges.

    Returns:
        MuscleGroupRead: The created muscle group data.

    Raises:
        ConflictException: If a muscle group with the same name already exists.
    """
    try:
        db_obj = await muscle_service.create(data=schema_data)
        muscle_group = muscle_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = f"A muscle group with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@muscle_router.get(
    path=urls.MUSCLE_GROUP_LIST,
    operation_id="ListMuscleGroups",
    name="muscles:list",
    summary="List of muscle groups.",
)
async def get_list_muscle_groups(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    muscle_service: MuscleGroupDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve all muscle groups with filtering and sorting.

    Returns:
        list[MuscleGroupRead]: A list of muscle group items.
    """
    muscle_groups = await muscle_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=muscle_groups)


@muscle_router.get(
    path=urls.MUSCLE_GROUP_DETAIL,
    operation_id="GetMuscleGroup",
    name="muscles:get",
    summary="Get muscle group details.",
)
async def get_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    muscle_service: MuscleGroupDep,
    muscle_id: int,
) -> MsgSpecJSONResponse:
    """Get information about a specific muscle group.

    Returns:
        MuscleGroupRead: Detailed muscle group data.

    Raises:
        NotFoundException: If the muscle group with the given ID does not exist.
    """
    try:
        db_obj = await muscle_service.get(item_id=muscle_id)
        muscle_group = muscle_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group)
    except NotFoundError as exc:
        msg = f"Muscle group with ID '{muscle_id}' not found"
        raise NotFoundException(message=msg) from exc


@muscle_router.patch(
    path=urls.MUSCLE_GROUP_UPDATE,
    operation_id="UpdateMuscleGroup",
    name="muscles:update",
    summary="Update muscle group.",
)
async def update_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_service: MuscleGroupDep,
    schema_data: MuscleGroupUpdate,
    muscle_id: int,
) -> MsgSpecJSONResponse:
    """Update information about a specific muscle group.

    Requires superuser privileges.

    Returns:
        MuscleGroupRead: The updated muscle group data.

    Raises:
        NotFoundException: If the muscle group with the given ID does not exist.
        ConflictException: If a muscle group with the same name already exists.
    """
    try:
        db_obj = await muscle_service.update(
            item_id=muscle_id,
            data=schema_data,
        )
        muscle_group = muscle_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = f"Muscle group with ID '{muscle_id}' not found"
            raise NotFoundException(message=msg) from exc
        msg = f"A muscle group with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@muscle_router.delete(
    path=urls.MUSCLE_GROUP_DELETE,
    operation_id="DeleteMuscleGroup",
    name="muscles:delete",
    summary="Delete a muscle group.",
)
async def delete_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_service: MuscleGroupDep,
    muscle_id: int,
) -> Response:
    """Remove a muscle group from the system.

    Requires superuser privileges.

    Returns:
        Response: 204 No Content on success.

    Raises:
        NotFoundException: If the muscle group with the given ID does not exist.
    """
    try:
        await muscle_service.delete(item_id=muscle_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        msg = f"Muscle group with ID '{muscle_id}' not found"
        raise NotFoundException(message=msg) from exc
