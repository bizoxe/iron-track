from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from advanced_alchemy.extensions.fastapi import repository, service
from advanced_alchemy.repository import Empty, EmptyType, ErrorMessages
from cashews import cache
from msgspec import convert
from sqlalchemy.exc import IntegrityError

from app.config.base import get_settings
from app.db import models as m
from app.domain.catalogs.schemas import (
    EquipmentList,
    EquipmentRead,
    MuscleGroupList,
    MuscleGroupRead,
    TagList,
    TagRead,
)
from app.lib.exceptions import ConflictException, NotFoundException

if TYPE_CHECKING:
    from collections.abc import Iterable

    from advanced_alchemy.repository import LoadSpec
    from advanced_alchemy.service import ModelDictT
    from advanced_alchemy.utils.serialization import SchemaDumpConfig
    from sqlalchemy.orm import InstrumentedAttribute
    from sqlalchemy.sql.selectable import ForUpdateParameter

    from app.db.models.catalog import CatalogBase
    from app.domain.catalogs.filters import CatalogFilters, CatalogFiltersWithRetired
    from app.domain.catalogs.schemas import CatalogList, CatalogReadBase


class BaseCatalogService[CatalogT: CatalogBase, ReadSchemaT: CatalogReadBase](
    service.SQLAlchemyAsyncRepositoryService[CatalogT]
):
    """Base service for managing soft-deletable catalog data with caching."""

    read_schema: type[ReadSchemaT]
    list_envelope: type[CatalogList[ReadSchemaT]]

    async def create(
        self,
        data: ModelDictT[CatalogT],
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
        bind_group: str | None = None,
        schema_dump_config: SchemaDumpConfig | None = None,
    ) -> CatalogT:
        """Create a new catalog item and invalidate cache.

        Raises:
            DuplicateKeyError: If an item with the same name already exists.
        """
        obj = await super().create(
            data=data,
            auto_commit=auto_commit,
            auto_expunge=True,
            auto_refresh=False,
            error_messages=error_messages,
        )
        await self._invalidate_cache()
        return obj

    async def update(
        self,
        data: ModelDictT[CatalogT],
        item_id: Any | None = None,
        *,
        attribute_names: Iterable[str] | None = None,
        with_for_update: ForUpdateParameter = None,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
        id_attribute: str | InstrumentedAttribute[Any] | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        uniquify: bool | None = None,
        bind_group: str | None = None,
        schema_dump_config: SchemaDumpConfig | None = None,
    ) -> CatalogT:
        """Update a catalog item and invalidate cache.

        Raises:
            NotFoundError: If the catalog item does not exist.
            DuplicateKeyError: If an item with the same name already exists.
        """
        obj = await super().update(
            data=data,
            item_id=item_id,
            attribute_names=attribute_names,
            id_attribute=id_attribute,
            load=load,
            execution_options=execution_options,
            with_for_update=with_for_update,
            auto_commit=auto_commit,
            auto_expunge=True,
            auto_refresh=False,
            error_messages=error_messages,
            uniquify=uniquify,
        )
        await self._invalidate_cache()
        return obj

    async def retire(
        self,
        item_id: int,
        *,
        error_prefix: str,
    ) -> None:
        """Retire a catalog item and invalidate cache.

        Raises:
            NotFoundException: If the catalog item does not exist.
        """
        db_obj = await self.get_one_or_none(id=item_id)
        if db_obj is None:
            raise NotFoundException(message=f"{error_prefix} not found")

        db_obj.deleted_at = datetime.now(tz=UTC)
        await self.repository.session.flush()
        await self._invalidate_cache()

    async def restore(
        self,
        item_id: int,
        data: dict[str, Any],
        *,
        error_prefix: str,
        error_entity: str,
    ) -> CatalogT:
        """Restore a retired catalog item and invalidate cache.

        Raises:
            NotFoundException: If the catalog item does not exist.
            ConflictException: If the item is not retired or an item with the same name already exists.
        """
        db_obj = await self.get_one_or_none(
            id=item_id,
            execution_options={"include_deleted": True},
        )
        if db_obj is None:
            raise NotFoundException(message=f"{error_prefix} not found")
        if db_obj.deleted_at is None:
            raise ConflictException(message=f"{error_prefix} is not retired")

        for field, value in data.items():
            setattr(db_obj, field, value)
        db_obj.deleted_at = None
        try:
            await self.repository.session.flush()
        except IntegrityError as exc:
            msg = f"{error_entity} with the same name already exists"
            raise ConflictException(message=msg) from exc
        await self._invalidate_cache()

        return db_obj

    async def get_list_items(
        self,
        params: CatalogFilters,
    ) -> list[ReadSchemaT]:
        """Retrieve a list of catalog items from database or cache."""
        return (await self._get_list_envelope(params)).items

    async def get_list_with_retired_items(
        self,
        params: CatalogFiltersWithRetired,
    ) -> list[ReadSchemaT]:
        """Retrieve a list of catalog items from database, including retired items."""
        filters = params.as_aa_filters
        data = await self.get_many(
            *filters,
            execution_options={"include_deleted": True},
        )
        return convert(data, type=list[self.read_schema], from_attributes=True)  # type: ignore[name-defined]

    # Key prefix is coupled to _invalidate_cache's delete_match pattern.
    @cache(
        ttl=get_settings().app.CATALOG_LIST_CACHE_TTL,
        key="{self.model_type.__tablename__}:{params}",
    )
    async def _get_list_envelope(self, params: CatalogFilters) -> CatalogList[ReadSchemaT]:
        """Fetch and cache the catalog list as a per-entity envelope."""
        filters = params.as_aa_filters
        data = await self.get_many(*filters)
        items = convert(data, type=list[self.read_schema], from_attributes=True)  # type: ignore[name-defined]
        return self.list_envelope(items=items)

    async def _invalidate_cache(self) -> None:
        """Remove the catalog data from the associated cache."""
        table_name = self.model_type.__tablename__
        await cache.delete_match(pattern=f"{table_name}:*")


class MuscleGroupService(BaseCatalogService[m.MuscleGroup, MuscleGroupRead]):
    """Handles database operations for muscle groups."""

    class MuscleGroupRepository(repository.SQLAlchemyAsyncRepository[m.MuscleGroup]):
        """Muscle group SQLAlchemy Repository."""

        model_type = m.MuscleGroup

    repository_type = MuscleGroupRepository
    read_schema = MuscleGroupRead
    list_envelope = MuscleGroupList


class EquipmentService(BaseCatalogService[m.Equipment, EquipmentRead]):
    """Handles database operations for equipment."""

    class EquipmentRepository(repository.SQLAlchemyAsyncRepository[m.Equipment]):
        """Equipment SQLAlchemy Repository."""

        model_type = m.Equipment

    repository_type = EquipmentRepository
    read_schema = EquipmentRead
    list_envelope = EquipmentList


class TagService(BaseCatalogService[m.Tag, TagRead]):
    """Handles database operations for exercise tags."""

    class TagRepository(repository.SQLAlchemyAsyncRepository[m.Tag]):
        """Exercise tags SQLAlchemy Repository."""

        model_type = m.Tag

    repository_type = TagRepository
    read_schema = TagRead
    list_envelope = TagList
