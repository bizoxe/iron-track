"""Exercise Tags Management Endpoints.

Provides functionality for managing exercise tags.

Exercise tags are strictly system-wide identifiers used solely for classifying
and searching system exercises.

Users cannot associate tags with their custom exercises.
Creating, updating, retiring, or restoring tags requires superuser privileges.
Reading tag data is available to all users.
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
from app.domain.catalogs.deps import TagDep
from app.domain.catalogs.filters import CatalogFilters, CatalogFiltersWithRetired
from app.domain.catalogs.schemas import TagCreate, TagRead, TagRestore, TagUpdate
from app.lib.exceptions import ConflictException, NotFoundException
from app.lib.json_response import MsgSpecJSONResponse
from app.lib.openapi_helpers import response_spec, response_spec_list
from app.lib.schema import ErrorInfo

exercise_tags_router = APIRouter(
    tags=["Catalogs: Exercise Tags"],
)


@exercise_tags_router.post(
    path=urls.EXERCISE_TAG_CREATE,
    operation_id="CreateTag",
    name="exercise_tags:create",
    summary="Create tag",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: response_spec(schema=TagRead, description="Created"),
        409: {
            "model": ErrorInfo,
        },
    },
)
async def create_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    tags_service: TagDep,
    data: TagCreate,
) -> MsgSpecJSONResponse:
    """Create a new exercise tag.

    Requires superuser privileges.
    """
    try:
        db_obj = await tags_service.create(data=data.model_dump())
        tag = tags_service.to_schema(db_obj, schema_type=TagRead)
        return MsgSpecJSONResponse(content=tag, status_code=status.HTTP_201_CREATED)
    except DuplicateKeyError as exc:
        msg = "An exercise tag with the same name already exists"
        raise ConflictException(message=msg) from exc


@exercise_tags_router.get(
    path=urls.EXERCISE_TAG_LIST,
    operation_id="ListTags",
    name="exercise_tags:list",
    summary="List of tags",
    responses={200: response_spec_list(schema=TagRead)},
)
async def get_list_exercise_tags(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    tags_service: TagDep,
    params: Annotated[CatalogFilters, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of exercise tags.

    Visibility:

    * Only active exercise tags are returned.
    """
    tags = await tags_service.get_list_items(params=params)
    return MsgSpecJSONResponse(content=tags)


@exercise_tags_router.get(
    path=urls.EXERCISE_TAG_WITH_RETIRED_LIST,
    operation_id="ListTagsWithRetired",
    name="exercise_tags:list-with-retired",
    summary="List of tags including retired",
    responses={200: response_spec_list(schema=TagRead)},
)
async def get_list_with_retired_exercise_tags(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    tags_service: TagDep,
    params: Annotated[CatalogFiltersWithRetired, Query()],
) -> MsgSpecJSONResponse:
    """Retrieve a list of exercise tags with retired items.

    Requires superuser privileges.

    Visibility:

    * Active and retired exercise tags are returned.
    """
    tags = await tags_service.get_list_with_retired_items(params=params)
    return MsgSpecJSONResponse(content=tags)


@exercise_tags_router.get(
    path=urls.EXERCISE_TAG_DETAIL,
    operation_id="GetTag",
    name="exercise_tags:get",
    summary="Get tag",
    responses={
        200: response_spec(schema=TagRead),
        404: {
            "model": ErrorInfo,
        },
    },
)
async def get_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.get_current_active_user())],
    tags_service: TagDep,
    tag_id: int,
) -> MsgSpecJSONResponse:
    """Retrieve exercise tag by ID.

    Visibility:

    * Only active exercise tags are returned.
    """
    try:
        db_obj = await tags_service.get(item_id=tag_id)
        tag = tags_service.to_schema(db_obj, schema_type=TagRead)
        return MsgSpecJSONResponse(content=tag)
    except NotFoundError as exc:
        msg = "Exercise tag not found"
        raise NotFoundException(message=msg) from exc


@exercise_tags_router.patch(
    path=urls.EXERCISE_TAG_UPDATE,
    operation_id="UpdateTag",
    name="exercise_tags:update",
    summary="Update tag",
    responses={
        200: response_spec(schema=TagRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def update_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    tags_service: TagDep,
    tag_id: int,
    data: TagUpdate,
) -> MsgSpecJSONResponse:
    """Update exercise tag by ID.

    Requires superuser privileges.
    """
    try:
        db_obj = await tags_service.update(
            item_id=tag_id,
            data=data.model_dump(),
        )
        tag = tags_service.to_schema(db_obj, schema_type=TagRead)
        return MsgSpecJSONResponse(content=tag)
    except (NotFoundError, DuplicateKeyError) as exc:
        if isinstance(exc, NotFoundError):
            msg = "Exercise tag not found"
            raise NotFoundException(message=msg) from exc
        msg = "An exercise tag with the same name already exists"
        raise ConflictException(message=msg) from exc


@exercise_tags_router.patch(
    path=urls.EXERCISE_TAG_RESTORE,
    operation_id="RestoreTag",
    name="exercise_tags:restore",
    summary="Restore tag",
    responses={
        200: response_spec(schema=TagRead, description="Updated"),
        404: {
            "model": ErrorInfo,
        },
        409: {
            "model": ErrorInfo,
        },
    },
)
async def restore_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    tags_service: TagDep,
    tag_id: int,
    data: TagRestore,
) -> MsgSpecJSONResponse:
    """Restore a retired exercise tag, optionally renaming it.

    Requires superuser privileges.

    A name change may be required if the original name is already used
    by another active exercise tag.
    """
    db_obj = await tags_service.restore(
        item_id=tag_id,
        data=data.model_dump(exclude_unset=True),
        error_prefix="Exercise tag",
        error_entity="An exercise tag",
    )
    tag = tags_service.to_schema(db_obj, schema_type=TagRead)
    return MsgSpecJSONResponse(content=tag)


@exercise_tags_router.delete(
    path=urls.EXERCISE_TAG_DELETE,
    operation_id="DeleteTag",
    name="exercise_tags:delete",
    summary="Retire tag",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        404: {
            "model": ErrorInfo,
        },
    },
)
async def delete_exercise_tag(
    _: Annotated[UserAuth, Depends(Authenticate.superuser_required())],
    tags_service: TagDep,
    tag_id: int,
) -> Response:
    """Retire an exercise tag.

    Requires superuser privileges.
    """
    await tags_service.retire(
        item_id=tag_id,
        error_prefix="Exercise tag",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
