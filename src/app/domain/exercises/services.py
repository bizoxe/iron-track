from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    NoReturn,
    cast,
)

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import (
    repository,
    service,
)
from advanced_alchemy.service import (
    ModelDictT,
    OffsetPagination,
    schema_dump,
)
from cashews import cache
from sqlalchemy import delete
from sqlalchemy.orm import (
    load_only,
    noload,
    raiseload,
    selectinload,
)

from app.db import models as m
from app.domain.catalogs.services import (
    BaseCatalogService,
    EquipmentService,
    ExerciseTagService,
    MuscleGroupService,
)
from app.domain.exercises.schemas import ExerciseRead
from app.lib.deps import (
    CacheKeyBuilder,
    CompositeServiceMixin,
)
from app.lib.exceptions import (
    BadRequestException,
    NotFoundException,
    PermissionDeniedException,
)

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.catalogs.schemas import FieldsReadBase
    from app.domain.exercises.utils import ExerciseFilters
    from app.domain.users.schemas import UserAuth


class ExerciseService(CompositeServiceMixin, service.SQLAlchemyAsyncRepositoryService[m.Exercise]):
    """Service for managing Exercise entities.

    Provides high-level business logic for exercises, including handling complex relationships
    with muscle groups, equipment, and tags via CompositeServiceMixin.
    """

    class ExerciseRepository(repository.SQLAlchemyAsyncRepository[m.Exercise]):
        """Exercise SQLAlchemy Repository."""

        model_type = m.Exercise

    repository_type = ExerciseRepository

    _rel_keys = ("primary_muscles", "secondary_muscles", "equipment", "tags")

    @property
    def muscles(self) -> MuscleGroupService:
        return self._get_service(MuscleGroupService)

    @property
    def equipment(self) -> EquipmentService:
        return self._get_service(EquipmentService)

    @property
    def tags(self) -> ExerciseTagService:
        return self._get_service(ExerciseTagService)

    async def to_model_on_create(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        return await self._populate_model(data)

    async def to_model_on_update(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        return await self._populate_model(data)

    async def to_model_on_upsert(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        return await self._populate_model(data)

    async def _validate_and_populate_fields(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        primary_ids = set(data.get("primary_muscles") or [])
        secondary_ids = set(data.get("secondary_muscles") or [])
        if all_muscles_ids := primary_ids | secondary_ids:
            all_cached_muscles = await self.muscles.get_all_cached()
            found_muscles = [obj for obj in all_cached_muscles if obj.id in all_muscles_ids]
            if len(found_muscles) != len(all_muscles_ids):
                found_ids = {obj.id for obj in found_muscles}
                self._raise_muscle_not_found(primary_ids - found_ids, secondary_ids - found_ids)
            muscles = await self.muscles.get_managed_objs(
                target_objs=found_muscles,
            )
            if "primary_muscles" in data:
                data["primary_muscles"] = [prim for prim in muscles if prim.id in primary_ids]
            if "secondary_muscles" in data:
                data["secondary_muscles"] = [sec for sec in muscles if sec.id in secondary_ids]

        services: list[tuple[str, BaseCatalogService[Any, Any]]] = [
            ("equipment", self.equipment),
            ("tags", self.tags),
        ]
        for key, serv in services:
            if requested_ids := set(data.get(key) or []):
                cached_items = await serv.get_all_cached()
                found_items = self._validate_ids(
                    requested_ids=requested_ids,
                    cached_data=cached_items,
                    error_prefix=key.capitalize(),
                )
                data[key] = await serv.get_managed_objs(target_objs=found_items)

        return data

    @staticmethod
    def _raise_muscle_not_found(
        missing_prim: set[int],
        missing_sec: set[int],
    ) -> NoReturn:
        if missing_prim and missing_sec:
            msg = f"Primary {list(missing_prim)} and secondary {list(missing_sec)} muscles not found"
        elif missing_prim:
            msg = f"Primary muscles not found: {list(missing_prim)}"
        else:
            msg = f"Secondary muscles not found: {list(missing_sec)}"
        raise NotFoundException(message=msg)

    @staticmethod
    def _validate_ids(
        requested_ids: set[int],
        cached_data: list[FieldsReadBase],
        error_prefix: str,
    ) -> list[FieldsReadBase]:
        """Validate muscle/equipment/tag IDs and replace them with model instances."""
        found = [obj for obj in cached_data if obj.id in requested_ids]

        if len(found) != len(requested_ids):
            found_ids = {obj.id for obj in found}
            missing = list(requested_ids - found_ids)
            raise NotFoundException(message=f"{error_prefix} not found: {missing}")

        return found

    async def _populate_model(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        data = schema_dump(data)
        data = await self._validate_and_populate_fields(data)
        model = await self.to_model(data, operation=None)

        for key in self._rel_keys:
            if key in data:
                setattr(model, key, data[key])

        return model

    async def get_exercise_by_filter(
        self,
        user_id: UUID,
        name: str | None,
        slug: str | None,
    ) -> ExerciseRead:
        """Fetch a specific exercise by name (for custom) or slug (for system)."""
        if name and slug:
            msg = "You must specify only one of the following: slug or name."
            raise BadRequestException(message=msg)
        ex_filter: dict[str, Any] = {}
        if name:
            ex_filter.update({"name": name, "created_by": user_id})
        if slug:
            ex_filter.update({"slug": slug, "is_system_default": True})
        try:
            db_obj = await self.get_one(**ex_filter)
            return self.to_schema(db_obj, schema_type=ExerciseRead)
        except NotFoundError as exc:
            msg = f"Exercise with {slug or name} not found"
            raise NotFoundException(message=msg) from exc

    async def update_exercise(
        self,
        exercise_id: UUID,
        data: dict[str, Any],
        extra_filters: dict[str, Any],
    ) -> m.Exercise:
        """Update an exercise with optimized relationship loading."""
        exists = await self.exists(id=exercise_id, **extra_filters)
        if not exists:
            msg = "Exercise not found"
            raise NotFoundException(message=msg)
        return await self.update(
            data=data,
            item_id=exercise_id,
            load=[
                selectinload(m.Exercise.primary_muscles),
                selectinload(m.Exercise.secondary_muscles),
                selectinload(m.Exercise.equipment),
                selectinload(m.Exercise.tags) if extra_filters.get("is_system_default") else noload(m.Exercise.tags),
            ],
            auto_refresh=False,
        )

    async def delete_exercise(
        self,
        exercise_id: UUID,
        user_auth: UserAuth,
    ) -> None:
        """Delete an exercise after checking ownership or superuser status.

        Deleting system-default exercises requires superuser privileges.
        """
        db_obj = await self.get_one_or_none(
            id=exercise_id,
            load=[
                load_only(m.Exercise.id, m.Exercise.created_by, m.Exercise.is_system_default),
                raiseload("*"),
            ],
        )
        if db_obj is None:
            msg = "Exercise not found"
            raise NotFoundException(message=msg)

        if (db_obj.is_system_default and not user_auth.is_superuser) or (
            not db_obj.is_system_default and db_obj.created_by != user_auth.id
        ):
            msg = "You do not have permission to delete this exercise"
            raise PermissionDeniedException(message=msg)

        stmt = delete(m.Exercise).where(m.Exercise.id == exercise_id)
        await self.repository.session.execute(stmt)

    async def get_exercises_paginated_dto(
        self,
        params: ExerciseFilters,
        user_id: UUID,
    ) -> OffsetPagination[ExerciseRead]:
        """Provide filtered and paginated list of exercises with caching."""
        params_key = CacheKeyBuilder.for_exercises(params=params, user_id=user_id)
        cached_data = await cache.get(key=params_key)
        if not cached_data:
            filters = params.build_exercise_filters(user_id=user_id)
            results, total = await self.list_and_count(*filters)
            exercises = self.to_schema(data=results, total=total, filters=filters, schema_type=ExerciseRead)
            await cache.set(key=params_key, value=exercises, expire="3m")
            return exercises

        return cast("OffsetPagination[ExerciseRead]", cached_data)
