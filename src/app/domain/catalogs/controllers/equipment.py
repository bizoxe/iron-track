"""Equipment Management Endpoints.

Provides functionality for CRUD operations on fitness equipment.

Creating, updating, and deleting equipment entries requires superuser privileges.
Reading equipment data is available to all authenticated users.
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
from app.domain.catalogs.deps import EquipmentDep
from app.domain.catalogs.schemas import (
    EquipmentCreate,
    EquipmentRead,
    EquipmentUpdate,
)
from app.domain.catalogs.utils import CatalogFilters
from app.domain.users.auth import Authenticate
from app.domain.users.schemas import UserAuth
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
)
from app.lib.json_response import MsgSpecJSONResponse

equipment_router = APIRouter(
    tags=["Equipment"],
)


@equipment_router.post(
    path=urls.EQUIPMENT_CREATE,
    operation_id="CreateEquipment",
    name="equipment:create",
    summary="Create new equipment.",
)
async def create_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    schema_data: EquipmentCreate,
) -> MsgSpecJSONResponse:
    """Create a new equipment entry.

    Requires superuser privileges.

    Returns:
        EquipmentRead: The created equipment data.

    Raises:
        ConflictException: If equipment with the same name already exists.
    """
    try:
        db_obj = await equipment_service.create(data=schema_data)
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = f"An equipment with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@equipment_router.get(
    path=urls.EQUIPMENT_LIST,
    operation_id="ListEquipment",
    name="equipment:list",
    summary="List of equipment.",
)
async def get_list_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    equipment_service: EquipmentDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve all equipment with filtering and sorting.

    Returns:
        list[EquipmentRead]: A list of equipment items.
    """
    equipment = await equipment_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=equipment)


@equipment_router.get(
    path=urls.EQUIPMENT_DETAIL,
    operation_id="GetEquipment",
    name="equipment:get",
    summary="Get equipment details.",
)
async def get_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    equipment_service: EquipmentDep,
    equipment_id: int,
) -> MsgSpecJSONResponse:
    """Get information about specific equipment.

    Returns:
        EquipmentRead: Detailed equipment data.

    Raises:
        NotFoundException: If equipment with the given ID does not exist.
    """
    try:
        db_obj = await equipment_service.get(item_id=equipment_id)
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment)
    except NotFoundError as exc:
        msg = f"Equipment with ID '{equipment_id}' not found"
        raise NotFoundException(message=msg) from exc


@equipment_router.patch(
    path=urls.EQUIPMENT_UPDATE,
    operation_id="UpdateEquipment",
    name="equipment:update",
    summary="Update equipment.",
)
async def update_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    schema_data: EquipmentUpdate,
    equipment_id: int,
) -> MsgSpecJSONResponse:
    """Update information about specific equipment.

    Requires superuser privileges.

    Returns:
        EquipmentRead: The updated equipment data.

    Raises:
        NotFoundException: If equipment with the given ID does not exist.
        ConflictException: If equipment with the same name already exists.
    """
    try:
        db_obj = await equipment_service.update(
            item_id=equipment_id,
            data=schema_data,
        )
        equipment = equipment_service.to_schema(db_obj, schema_type=EquipmentRead)
        return MsgSpecJSONResponse(content=equipment)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = f"Equipment with ID '{equipment_id}' not found"
            raise NotFoundException(message=msg) from exc
        msg = f"An equipment with the name '{schema_data.name}' already exists"
        raise ConflictException(message=msg) from exc


@equipment_router.delete(
    path=urls.EQUIPMENT_DELETE,
    operation_id="DeleteEquipment",
    name="equipment:delete",
    summary="Delete equipment.",
)
async def delete_equipment(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    equipment_service: EquipmentDep,
    equipment_id: int,
) -> Response:
    """Remove equipment from the system.

    Requires superuser privileges.

    Returns:
        Response: 204 No Content on success.

    Raises:
        NotFoundException: If equipment with the given ID does not exist.
    """
    try:
        await equipment_service.delete(item_id=equipment_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundError as exc:
        msg = f"Equipment with ID '{equipment_id}' not found"
        raise NotFoundException(message=msg) from exc
