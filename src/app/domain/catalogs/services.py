from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from advanced_alchemy.base import DefaultBase
from advanced_alchemy.extensions.fastapi import (
    repository,
    service,
)
from advanced_alchemy.repository import (
    Empty,
    EmptyType,
    ErrorMessages,
    LoadSpec,
)
from cashews import cache
from msgspec import (
    Struct,
    convert,
    to_builtins,
)
from sqlalchemy.orm import make_transient_to_detached

from app.config.constants import (
    CATALOG_ALL_CACHE_TTL,
    CATALOG_LIST_CACHE_TTL,
)
from app.db import models as m
from app.domain.catalogs.schemas import (
    EquipmentRead,
    ExerciseTagRead,
    MuscleGroupRead,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from advanced_alchemy.service import ModelDictT
    from advanced_alchemy.service.typing import BulkModelDictT
    from sqlalchemy.orm import InstrumentedAttribute
    from sqlalchemy.sql.selectable import ForUpdateParameter

    from app.domain.catalogs.utils import CatalogFilters


class BaseCatalogService[T: DefaultBase, S: Struct](service.SQLAlchemyAsyncRepositoryService[T]):
    """Base service for managing catalog data with automated caching."""

    read_schema: type[S]

    @cache(
        ttl=CATALOG_LIST_CACHE_TTL,
        key="{self.model_type.__tablename__}:{params}",
    )
    async def get_list_items(
        self,
        params: CatalogFilters,
    ) -> list[S]:
        """Retrieve a list of catalog items from database or cache with filtering."""
        filters = params.aa_filters
        data = await self.list(*filters)
        return convert(data, type=list[self.read_schema], from_attributes=True)  # type: ignore[name-defined]

    @cache(
        ttl=CATALOG_ALL_CACHE_TTL,
        key="{self.model_type.__tablename__}:all",
    )
    async def get_all_cached(self) -> list[S]:
        """Retrieve all catalog items from cache or database."""
        data = await self.list()
        return convert(data, type=list[self.read_schema], from_attributes=True)  # type: ignore[name-defined]

    async def _invalidate_cache(self) -> None:
        """Remove the catalog data from the associated cache."""
        table_name = self.model_type.__tablename__
        await cache.delete_match(pattern=f"{table_name}:*")

    async def get_managed_objs(self, target_objs: list[S]) -> list[T]:
        """Merge detached catalog data into the current session without DB hits."""
        managed_objs = []
        for obj in target_objs:
            model_obj = self.repository.model_type(**to_builtins(obj))
            make_transient_to_detached(model_obj)
            merged = await self.repository.session.merge(model_obj, load=False)
            managed_objs.append(merged)

        return managed_objs

    async def upsert_many(
        self,
        data: BulkModelDictT[T],
        *,
        auto_expunge: bool | None = None,
        auto_commit: bool | None = None,
        no_merge: bool = False,
        match_fields: list[str] | str | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        uniquify: bool | None = None,
    ) -> Sequence[T]:
        """Upsert multiple records and invalidate the associated cache."""
        objs = await super().upsert_many(
            data,
            auto_expunge=auto_expunge,
            auto_commit=auto_commit,
            no_merge=no_merge,
            match_fields=match_fields,
            error_messages=error_messages,
            load=load,
            execution_options=execution_options,
            uniquify=uniquify,
        )
        await self._invalidate_cache()
        return objs

    async def create(
        self,
        data: ModelDictT[T],
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
    ) -> T:
        """Create a new catalog item and invalidate cache."""
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
        data: ModelDictT[T],
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
    ) -> T:
        """Update a catalog item and invalidate cache."""
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

    async def delete(
        self,
        item_id: Any,
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        id_attribute: str | InstrumentedAttribute[Any] | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        uniquify: bool | None = None,
    ) -> T:
        """Delete a catalog item and invalidate cache."""
        obj = await super().delete(
            item_id=item_id,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            id_attribute=id_attribute,
            error_messages=error_messages,
            load=load,
            execution_options=execution_options,
            uniquify=uniquify,
        )
        await self._invalidate_cache()
        return obj


class MuscleGroupService(BaseCatalogService[m.MuscleGroup, MuscleGroupRead]):
    """Handles database operations for muscle groups."""

    class MuscleGroupRepository(repository.SQLAlchemyAsyncRepository[m.MuscleGroup]):
        """Muscle group SQLAlchemy Repository."""

        model_type = m.MuscleGroup

    repository_type = MuscleGroupRepository
    read_schema = MuscleGroupRead


class EquipmentService(BaseCatalogService[m.Equipment, EquipmentRead]):
    """Handles database operations for equipment."""

    class EquipmentRepository(repository.SQLAlchemyAsyncRepository[m.Equipment]):
        """Equipment SQLAlchemy Repository."""

        model_type = m.Equipment

    repository_type = EquipmentRepository
    read_schema = EquipmentRead


class ExerciseTagService(BaseCatalogService[m.ExerciseTag, ExerciseTagRead]):
    """Handles database operations for exercise tags."""

    class ExerciseTagRepository(repository.SQLAlchemyAsyncRepository[m.ExerciseTag]):
        """Exercise tags SQLAlchemy Repository."""

        model_type = m.ExerciseTag

    repository_type = ExerciseTagRepository
    read_schema = ExerciseTagRead
