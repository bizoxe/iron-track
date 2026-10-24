from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

from advanced_alchemy.base import DefaultBase
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import repository, service
from advanced_alchemy.repository import Empty, EmptyType, ErrorMessages
from advanced_alchemy.service import schema_dump
from cashews import cache
from sqlalchemy import select
from sqlalchemy.orm import load_only, noload

from app.db import models as m
from app.domain.catalogs.services import (
    EquipmentService,
    MuscleGroupService,
    TagService,
)
from app.domain.enums import MuscleRole
from app.domain.exercises.schemas import ExerciseRead, ExerciseScope
from app.domain.exercises.utils import can_delete_exercise, slugify
from app.lib.deps import (
    CacheKeyBuilder,
    CompositeServiceMixin,
)
from app.lib.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from uuid import UUID

    from advanced_alchemy.repository import LoadSpec
    from advanced_alchemy.service import ModelDictT, OffsetPagination
    from advanced_alchemy.service.typing import SchemaDumpConfig
    from sqlalchemy.orm import InstrumentedAttribute
    from sqlalchemy.sql.selectable import ForUpdateParameter

    from app.domain.accounts.schemas import UserAuth
    from app.domain.exercises.filters import ExerciseFilters


class ExerciseService(CompositeServiceMixin, service.SQLAlchemyAsyncRepositoryService[m.Exercise]):
    """Handles database operations for exercises.

    Composes catalog services (muscle groups, equipment, tags) via
    CompositeServiceMixin; composed services share the parent's session.
    """

    class ExerciseRepository(repository.SQLAlchemyAsyncRepository[m.Exercise]):
        """Exercise SQLAlchemy Repository."""

        model_type = m.Exercise

    repository_type = ExerciseRepository

    @property
    def muscles(self) -> MuscleGroupService:
        return self._get_service(MuscleGroupService)

    @property
    def equipment(self) -> EquipmentService:
        return self._get_service(EquipmentService)

    @property
    def tags(self) -> TagService:
        return self._get_service(TagService)

    async def to_model_on_create(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        # Create path: catalogs + junction rows (full replacement — no existing rows).
        return await self._prepare_data(schema_dump(data))

    async def to_model_on_update(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        # Update path: catalogs only. Muscle keys are popped by the update() override
        # before to_model runs — they need object-aware merge, not payload replacement.
        return await self._prepare_data(schema_dump(data))

    async def to_model_on_upsert(self, data: ModelDictT[m.Exercise]) -> ModelDictT[m.Exercise]:
        # Upsert path: payload shape matches create (insert branch carries the junction).
        return await self._prepare_data(schema_dump(data))

    # --- Public API ---

    async def get_by_name(
        self,
        user_id: UUID,
        scope: Literal[ExerciseScope.USER, ExerciseScope.SYSTEM],
        name: str,
    ) -> m.Exercise:
        """Retrieve user-defined or system exercise by name.

        The name is normalized to a slug before lookup, so names that normalize
        to the same slug resolve to the same exercise.

        The scope determines the search space: ``USER`` searches exercises created
        by ``user_id``; ``SYSTEM`` searches system defaults and ignores ``user_id``.

        Raises:
            NotFoundException: If no exercise matches the normalized name in the given scope.
        """
        try:
            if scope == ExerciseScope.USER:
                db_obj = await self.get_one(
                    self.model_type.created_by == user_id,
                    slug=slugify(name),
                )
            else:
                db_obj = await self.get_one(
                    self.model_type.is_system_default.is_(True),
                    slug=slugify(name),
                )
        except NotFoundError as exc:
            msg = f"Exercise with '{name}' not found"
            raise NotFoundException(message=msg) from exc

        return db_obj

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
            results, total = await self.get_many_and_count(*filters)
            exercises = self.to_schema(data=results, total=total, filters=filters, schema_type=ExerciseRead)
            await cache.set(key=params_key, value=exercises, expire="3m")
            return exercises

        return cast("OffsetPagination[ExerciseRead]", cached_data)

    async def exercise_exists(
        self,
        exercise_id: UUID,
        created_by: UUID | None,
    ) -> bool:
        """Check existence under the caller's ownership scope (owner id or system)."""
        if created_by is not None:
            return await self.exists(
                self.model_type.id == exercise_id,
                self.model_type.created_by == created_by,
            )
        return await self.exists(
            self.model_type.id == exercise_id,
            self.model_type.is_system_default.is_(True),
        )

    async def update(
        self,
        data: ModelDictT[m.Exercise],
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
    ) -> m.Exercise:
        """Update exercise with role-aware junction merge for muscle lists.

        Advanced Alchemy's update() has no partial-collection contract: a collection
        key in the payload replaces the whole relationship, and the junction's
        ``muscle_role`` cannot be expressed by plain assignment — muscle keys are
        popped here and merged object-aware (see _merge_exercise_muscles).

        ``auto_commit`` is accepted for interface compatibility but never honored:
        this method relies on the outer session lifecycle to commit, so the junction
        merge shares one transaction with the scalar update. ``schema_dump_config`` is
        not forwarded — the payload is normalized to a dict before persistence.

        Raises:
            NotFoundException: If a referenced muscle group, equipment, or tag id does not exist.
            ConflictException: If the same muscle group is listed as both primary and secondary.
            DuplicateKeyError: If the resulting slug conflicts with an existing exercise.
        """
        data = schema_dump(data)
        primary_ids = data.pop("primary_muscles", None)  # None = untouched, [] = clear
        secondary_ids = data.pop("secondary_muscles", None)

        obj = await super().update(
            data,
            item_id=item_id,
            attribute_names=attribute_names,
            with_for_update=with_for_update,
            auto_commit=False,  # junction merge below must share this transaction
            auto_expunge=auto_expunge,
            auto_refresh=False,
            id_attribute=id_attribute,
            error_messages=error_messages,
            load=load,
            execution_options=execution_options,
            uniquify=uniquify,
            bind_group=bind_group,
        )

        if primary_ids is not None or secondary_ids is not None:
            await self._merge_exercise_muscles(obj, primary_ids, secondary_ids)
            await self.repository.session.flush()

        return obj

    async def delete_exercise(
        self,
        exercise_id: UUID,
        user_auth: UserAuth,
    ) -> None:
        """Delete an exercise after checking access permissions.

        Deletion relies on the outer session lifecycle to commit, same as
        ``update()``: ``session.delete()`` only stages the deletion, and the DELETE
        is issued during the flush triggered by the outer ``commit()``.

        Raises:
            NotFoundException: If the exercise is not found.
            PermissionDeniedException: If the user lacks permission to delete the exercise.
        """
        db_obj = await self.get_one_or_none(
            id=exercise_id,
            load=[
                load_only(self.model_type.id, self.model_type.created_by, self.model_type.is_system_default),
                noload("*"),
            ],
        )
        if db_obj is None:
            raise NotFoundException(message="Exercise not found")

        if not can_delete_exercise(
            exercise=db_obj,
            user=user_auth,
        ):
            msg = "You do not have permission to delete this exercise"
            raise PermissionDeniedException(message=msg)

        await self.repository.session.delete(db_obj)

    # --- Private helpers ---

    async def _prepare_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize the incoming payload: derive slug, resolve catalog references."""
        if data.get("name"):
            data["slug"] = slugify(data["name"])
        return await self._apply_catalogs(data)

    async def _apply_catalogs(self, data: dict[str, Any]) -> dict[str, Any]:
        """Single assembly point for catalog payload keys.

        Key present (even []) -> relationship replaced/cleared;
        Key absent            -> relationship untouched.

        Muscles: keys are popped by the update() override before to_model runs,
        so this branch is naturally create-path-only (no existing rows to merge).
        """
        if "primary_muscles" in data or "secondary_muscles" in data:
            role_by_id = await self._resolve_muscle_map(
                primary_ids=data.pop("primary_muscles", None),
                secondary_ids=data.pop("secondary_muscles", None),
            )
            data["exercise_muscles"] = [
                m.ExerciseMuscle(muscle_group=group, muscle_role=role) for _, (group, role) in role_by_id.items()
            ]

        catalogs: dict[str, tuple[service.SQLAlchemyAsyncRepositoryService[Any, Any], str]] = {
            "equipment": (self.equipment, "Equipment"),
            "tags": (self.tags, "Tag"),
        }
        for key, (catalog_service, error_prefix) in catalogs.items():
            if key in data:
                data[key] = await self._resolve_by_ids(catalog_service, ids=data[key], error_prefix=error_prefix)
        return data

    async def _resolve_muscle_map(
        self,
        primary_ids: Sequence[int] | None,
        secondary_ids: Sequence[int] | None,
    ) -> dict[int, tuple[m.MuscleGroup, MuscleRole]]:
        """Validate muscle ids (404) and map them to roles (409 on role conflict)."""
        primary = list(primary_ids or ())
        secondary = list(secondary_ids or ())
        if not primary and not secondary:
            return {}

        groups: list[m.MuscleGroup] = await self._resolve_by_ids(
            self.muscles, ids=[*primary, *secondary], error_prefix="Muscle group"
        )
        group_by_id = {group.id: group for group in groups}

        role_by_id: dict[int, tuple[m.MuscleGroup, MuscleRole]] = {}
        for group_id in primary:
            role_by_id[group_id] = (group_by_id[group_id], MuscleRole.PRIMARY)

        conflicting = [group_id for group_id in secondary if group_id in role_by_id]
        if conflicting:
            raise ConflictException(
                message="Muscle groups cannot be primary and secondary at the same time",
                details={"group_ids": sorted(conflicting)},
            )
        for group_id in secondary:
            role_by_id[group_id] = (group_by_id[group_id], MuscleRole.SECONDARY)

        return role_by_id

    async def _merge_exercise_muscles(
        self,
        exercise: m.Exercise,
        primary_ids: Sequence[int] | None,
        secondary_ids: Sequence[int] | None,
    ) -> None:
        """Merge role-scoped muscle lists into existing junction rows.

        None      -> rows of that role are kept untouched;
        []        -> rows of that role are removed (clear);
        non-empty -> rows of that role are replaced (same muscle may switch role in place).
        """
        if primary_ids is None and secondary_ids is None:
            return  # neither list passed -> pure no-op

        role_by_id = await self._resolve_muscle_map(primary_ids, secondary_ids)
        existing = {link.muscle_group_id: link for link in exercise.exercise_muscles}

        for group_id, link in existing.items():
            if group_id in role_by_id:
                _, role = role_by_id[group_id]
                if link.muscle_role is not role:
                    link.muscle_role = role  # same muscle, role switch -> UPDATE
            elif (link.muscle_role is MuscleRole.PRIMARY and primary_ids is not None) or (
                link.muscle_role is MuscleRole.SECONDARY and secondary_ids is not None
            ):
                exercise.exercise_muscles.remove(link)  # role list replaced without it -> DELETE

        for group_id, (group, role) in role_by_id.items():
            if group_id not in existing:
                exercise.exercise_muscles.append(
                    m.ExerciseMuscle(muscle_group=group, muscle_role=role)  # INSERT
                )

    async def _resolve_by_ids[E: DefaultBase](
        self,
        catalog_service: service.SQLAlchemyAsyncRepositoryService[Any, Any],
        ids: Sequence[int],
        *,
        error_prefix: str,
    ) -> list[E]:
        """Resolve id list into rows (404 listing missing ids). Empty list -> []."""
        wanted = set(ids)
        if not wanted:
            return []
        model_type = catalog_service.model_type
        found = await catalog_service.get_many(
            statement=select(model_type).where(model_type.id.in_(wanted)),
        )
        self._validate_ids(requested_ids=wanted, found_ids={row.id for row in found}, error_prefix=error_prefix)
        return list(found)

    @staticmethod
    def _validate_ids(
        *,
        requested_ids: set[int],
        found_ids: set[int],
        error_prefix: str,
    ) -> None:
        """Raise 404 listing ids that were requested but not found."""
        missing = requested_ids - found_ids
        if missing:
            raise NotFoundException(
                message=f"{error_prefix} not found",
                details={"missing_ids": sorted(missing)},
            )
