"""Equipment Management Endpoints.

Provides functionality for managing equipment.

Creating, updating, retiring, or restoring equipment requires
superuser privileges.
Reading equipment data is available to all users.
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
from app.domain.catalogs.deps import EquipmentDep
from app.domain.catalogs.filters import CatalogFilters, CatalogFiltersWithRetired
from app.domain.catalogs.schemas import (
    EquipmentCreate,
    EquipmentRead,
    EquipmentRestore,
    EquipmentUpdate,
)
from app.lib.exceptions import ConflictException, NotFoundException
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec, response_spec_list
from app.lib.schema import ErrorInfo

equipment_router = APIRouter(
    tags=["Catalogs: Equipment"],
)


@equipment_router.post(
    path=urls.EQUIPMENT_CREATE,
    operation_id="CreateEquipment",
    name="equipment:create",
    summary="Create equipment",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=EquipmentRead, description="Created"),
        409: {
            "model": ErrorInfo,
        },
    },
)
async def create_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    data: EquipmentCreate,
) -> MsgSpecJSONResponse:
    """Create new equipment.

    Requires superuser privileges.
    """
    try:
        db_obj = await equipment_service.create(data=data.model_dump())
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "Equipment with the same name already exists"
        raise ConflictException(message=msg) from exc


@equipment_router.get(
    path=urls.EQUIPMENT_LIST,
    operation_id="ListEquipment",
    name="equipment:list",
    summary="List of equipment",
    responses={200: response_spec_list(schema=EquipmentRead)},
)
async def get_list_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    equipment_service: EquipmentDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of equipment.

    Visibility:

    * Only active equipment is returned.
    """
    equipment = await equipment_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=equipment)


@equipment_router.get(
    path=urls.EQUIPMENT_WITH_RETIRED_LIST,
    operation_id="ListEquipmentWithRetired",
    name="equipment:list-with-retired",
    summary="List of equipment including retired",
    responses={200: response_spec_list(schema=EquipmentRead)},
)
async def get_list_with_retired_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    params: Annotated[CatalogFiltersWithRetired, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of equipment with retired items.

    Requires superuser privileges.

    Visibility:

    * Active and retired equipment are returned.
    """
    equipment = await equipment_service.get_list_with_retired_items(params=params)
    return MsgSpecJSONResponse(content=equipment)


@equipment_router.get(
    path=urls.EQUIPMENT_DETAIL,
    operation_id="GetEquipment",
    name="equipment:get",
    summary="Get equipment",
    responses={
        200: response_spec(schema=EquipmentRead),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    equipment_service: EquipmentDep,
    equipment_id: int,
) -> MsgSpecJSONResponse:
    """Retrieve equipment by ID.

    Visibility:

    * Only active equipment is returned.
    """
    try:
        db_obj = await equipment_service.get(item_id=equipment_id)
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment)
    except NotFoundError as exc:
        msg = "Equipment not found"
        raise NotFoundException(message=msg) from exc


@equipment_router.patch(
    path=urls.EQUIPMENT_UPDATE,
    operation_id="UpdateEquipment",
    name="equipment:update",
    summary="Update equipment",
    responses={
        200: response_spec(schema=EquipmentRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def update_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    equipment_id: int,
    data: EquipmentUpdate,
) -> MsgSpecJSONResponse:
    """Update equipment by ID.

    Requires superuser privileges.
    """
    try:
        db_obj = await equipment_service.update(
            item_id=equipment_id,
            data=data.model_dump(),
        )
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = "Equipment not found"
            raise NotFoundException(message=msg) from exc
        msg = "Equipment with the same name already exists"
        raise ConflictException(message=msg) from exc


@equipment_router.patch(
    path=urls.EQUIPMENT_RESTORE,
    operation_id="RestoreEquipment",
    name="equipment:restore",
    summary="Restore equipment",
    responses={
        200: response_spec(schema=EquipmentRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def restore_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    equipment_id: int,
    data: EquipmentRestore,
) -> MsgSpecJSONResponse:
    """Restore retired equipment, optionally renaming it.

    Requires superuser privileges.

    A name change may be required if the original name is already used
    by another active equipment item.
    """
    db_obj = await equipment_service.restore(
        item_id=equipment_id,
        data=data.model_dump(exclude_unset=True),
        error_prefix="Equipment",
        error_entity="Equipment",
    )
    equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
    return MsgSpecJSONResponse(content=equipment)


@equipment_router.delete(
    path=urls.EQUIPMENT_DELETE,
    operation_id="DeleteEquipment",
    name="equipment:delete",
    summary="Retire equipment",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        404: {
            "model": ErrorInfo,
        },
    },
)
async def delete_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    equipment_id: int,
) -> Response:
    """Retire equipment.

    Requires superuser privileges.
    """
    await equipment_service.retire(
        item_id=equipment_id,
        error_prefix="Equipment",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
