"""Muscle Group Endpoints.

Provides functionality for managing muscle groups.

Creating, updating, retiring, or restoring muscle groups requires
superuser privileges.
Reading muscle group data is available to all users.
"""

from typing import Annotated

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from app.domain.accounts.auth import Authenticate
from app.domain.accounts.schemas import UserAuth
from app.domain.catalogs import urls
from app.domain.catalogs.deps import MuscleGroupDep
from app.domain.catalogs.filters import CatalogFilters, CatalogFiltersWithRetired
from app.domain.catalogs.schemas import (
    MuscleGroupCreate,
    MuscleGroupRead,
    MuscleGroupRestore,
    MuscleGroupUpdate,
)
from app.lib.exceptions import ConflictException, NotFoundException
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec, response_spec_list
from app.lib.schema import ErrorInfo

muscle_groups_router = APIRouter(
    tags=["Catalogs: Muscle Groups"],
)


@muscle_groups_router.post(
    path=urls.MUSCLE_GROUP_CREATE,
    operation_id="CreateMuscleGroup",
    name="muscle_groups:create",
    summary="Create muscle group",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=MuscleGroupRead, description="Created"),
        409: {
            "model": ErrorInfo,
        },
    },
)
async def create_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_groups_service: MuscleGroupDep,
    data: MuscleGroupCreate,
) -> MsgSpecJSONResponse:
    """Create a new muscle group.

    Requires superuser privileges.
    """
    try:
        db_obj = await muscle_groups_service.create(data=data.model_dump())
        muscle_group = muscle_groups_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "A muscle group with the same name already exists"
        raise ConflictException(message=msg) from exc


@muscle_groups_router.get(
    path=urls.MUSCLE_GROUP_LIST,
    operation_id="ListMuscleGroups",
    name="muscle_groups:list",
    summary="List of muscle groups",
    responses={200: response_spec_list(schema=MuscleGroupRead)},
)
async def get_list_muscle_groups(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    muscle_groups_service: MuscleGroupDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of muscle groups.

    Visibility:

    * Only active muscle groups are returned.
    """
    muscle_groups = await muscle_groups_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=muscle_groups)


@muscle_groups_router.get(
    path=urls.MUSCLE_GROUP_WITH_RETIRED_LIST,
    operation_id="ListMuscleGroupsWithRetired",
    name="muscle_groups:list-with-retired",
    summary="List of muscle groups including retired",
    responses={200: response_spec_list(schema=MuscleGroupRead)},
)
async def get_list_with_retired_muscle_groups(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_groups_service: MuscleGroupDep,
    params: Annotated[CatalogFiltersWithRetired, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of muscle groups with retired items.

    Requires superuser privileges.

    Visibility:

    * Active and retired muscle groups are returned.
    """
    muscle_groups = await muscle_groups_service.get_list_with_retired_items(params=params)
    return MsgSpecJSONResponse(content=muscle_groups)


@muscle_groups_router.get(
    path=urls.MUSCLE_GROUP_DETAIL,
    operation_id="GetMuscleGroup",
    name="muscle_groups:get",
    summary="Get muscle group",
    responses={
        200: response_spec(schema=MuscleGroupRead),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    muscle_groups_service: MuscleGroupDep,
    muscle_id: int,
) -> MsgSpecJSONResponse:
    """Retrieve muscle group by ID.

    Visibility:

    * Only active muscle groups are returned.
    """
    try:
        db_obj = await muscle_groups_service.get(item_id=muscle_id)
        muscle_group = muscle_groups_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group)
    except NotFoundError as exc:
        msg = "Muscle group not found"
        raise NotFoundException(message=msg) from exc


@muscle_groups_router.patch(
    path=urls.MUSCLE_GROUP_UPDATE,
    operation_id="UpdateMuscleGroup",
    name="muscle_groups:update",
    summary="Update muscle group",
    responses={
        200: response_spec(schema=MuscleGroupRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def update_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_groups_service: MuscleGroupDep,
    muscle_id: int,
    data: MuscleGroupUpdate,
) -> MsgSpecJSONResponse:
    """Update muscle group by ID.

    Requires superuser privileges.
    """
    try:
        db_obj = await muscle_groups_service.update(
            item_id=muscle_id,
            data=data.model_dump(),
        )
        muscle_group = muscle_groups_service.to_schema(db_obj, schema_type=MuscleGroupRead)
        return MsgSpecJSONResponse(content=muscle_group)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = "Muscle group not found"
            raise NotFoundException(message=msg) from exc
        msg = "A muscle group with the same name already exists"
        raise ConflictException(message=msg) from exc


@muscle_groups_router.patch(
    path=urls.MUSCLE_GROUP_RESTORE,
    operation_id="RestoreMuscleGroup",
    name="muscle_groups:restore",
    summary="Restore muscle group",
    responses={
        200: response_spec(schema=MuscleGroupRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def restore_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_groups_service: MuscleGroupDep,
    muscle_id: int,
    data: MuscleGroupRestore,
) -> MsgSpecJSONResponse:
    """Restore a retired muscle group, optionally renaming it.

    Requires superuser privileges.

    A name change may be required if the original name is already used
    by another active muscle group.
    """
    db_obj = await muscle_groups_service.restore(
        item_id=muscle_id,
        data=data.model_dump(exclude_unset=True),
        error_prefix="Muscle group",
        error_entity="A muscle group",
    )
    muscle_group = muscle_groups_service.to_schema(db_obj, schema_type=MuscleGroupRead)
    return MsgSpecJSONResponse(content=muscle_group)


@muscle_groups_router.delete(
    path=urls.MUSCLE_GROUP_DELETE,
    operation_id="DeleteMuscleGroup",
    name="muscle_groups:delete",
    summary="Retire muscle group",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        404: {
            "model": ErrorInfo,
        },
    },
)
async def delete_muscle_group(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    muscle_groups_service: MuscleGroupDep,
    muscle_id: int,
) -> Response:
    """Retire a muscle group.

    Requires superuser privileges.
    """
    await muscle_groups_service.retire(
        item_id=muscle_id,
        error_prefix="Muscle group",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
