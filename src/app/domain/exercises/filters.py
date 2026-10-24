from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Annotated, Any, Literal

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import Field
from sqlalchemy import or_

from app.db import models as m
from app.domain.enums import Category, DifficultyLevel, MuscleRole
from app.domain.exercises.schemas import ExerciseScope
from app.lib.filters import CommonFilters

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from uuid import UUID


_SCOPE_STRATEGY: Mapping[ExerciseScope, Callable[[UUID], aa_filters.StatementFilter]] = MappingProxyType(
    {
        ExerciseScope.SYSTEM: lambda _: aa_filters.ComparisonFilter("is_system_default", "eq", value=True),
        ExerciseScope.USER: lambda uid: aa_filters.ComparisonFilter("created_by", "eq", uid),
        ExerciseScope.ALL: lambda uid: aa_filters.FilterGroup(
            logical_operator=or_,
            filters=[
                aa_filters.ComparisonFilter("is_system_default", "eq", value=True),
                aa_filters.ComparisonFilter("created_by", "eq", uid),
            ],
        ),
    }
)


class ExerciseFilters(CommonFilters):
    """Specific filters for Exercise domain."""

    order_by: Annotated[
        Literal["name", "category", "difficultyLevel"],
        Field(description="Field to order by."),
    ] = "name"
    scope: Annotated[
        ExerciseScope,
        Field(description="Data ownership scope (system/user/all)."),
    ] = ExerciseScope.ALL
    primary_muscles: Annotated[
        list[int] | None,
        Field(description="Primary muscle group IDs."),
    ] = None
    secondary_muscles: Annotated[
        list[int] | None,
        Field(description="Secondary muscle group IDs."),
    ] = None
    equipment: Annotated[
        list[int] | None,
        Field(description="Required equipment IDs."),
    ] = None
    tags: Annotated[
        list[int] | None,
        Field(description="Exercise tag IDs."),
    ] = None
    category: Annotated[
        Category | None,
        Field(description="Primary exercise categories."),
    ] = None
    difficulty_level: Annotated[
        DifficultyLevel | None,
        Field(description="Difficulty levels."),
    ] = None

    def build_exercise_filters(
        self,
        user_id: UUID,
    ) -> list[aa_filters.StatementFilter]:
        """Build statement filters from the exercise filter attributes.

        Args:
            user_id: The ID of the user requesting the exercises for scope filtering.

        Returns:
            list[StatementFilter]: A list of filters.
        """
        filters = [_SCOPE_STRATEGY[self.scope](user_id), *self.as_aa_filters]

        if self.primary_muscles:
            filters.append(self._muscle_role_filter(MuscleRole.PRIMARY, self.primary_muscles))
        if self.secondary_muscles:
            filters.append(self._muscle_role_filter(MuscleRole.SECONDARY, self.secondary_muscles))
        if self.equipment:
            filters.append(
                aa_filters.ExistsFilter(
                    values=[
                        m.exercise_equipment.c.exercise_id == m.Exercise.id,
                        m.exercise_equipment.c.equipment_id.in_(self.equipment),
                    ]
                )
            )
        if self.tags:
            filters.append(
                aa_filters.ExistsFilter(
                    values=[
                        m.exercise_tag.c.exercise_id == m.Exercise.id,
                        m.exercise_tag.c.tag_id.in_(self.tags),
                    ]
                )
            )
        if self.category:
            filters.append(aa_filters.ComparisonFilter(field_name="category", operator="eq", value=self.category))
        if self.difficulty_level:
            filters.append(
                aa_filters.ComparisonFilter(field_name="difficulty_level", operator="eq", value=self.difficulty_level)
            )

        return filters

    @staticmethod
    def _muscle_role_filter(
        role: MuscleRole,
        muscle_group_ids: list[int],
    ) -> aa_filters.ExistsFilter:
        return aa_filters.ExistsFilter(
            values=[
                m.ExerciseMuscle.exercise_id == m.Exercise.id,
                m.ExerciseMuscle.muscle_group_id.in_(muscle_group_ids),
                m.ExerciseMuscle.muscle_role == role,
            ],
        )

    def model_post_init(self, context: Any) -> None:
        """Extend the base cache key with exercise-specific filter parameters."""
        super().model_post_init(context)
        parts = [f":{self.scope}"]
        if self.primary_muscles:
            parts.append(f":p:{'-'.join(map(str, sorted(self.primary_muscles)))}")
        if self.secondary_muscles:
            parts.append(f":s:{'-'.join(map(str, sorted(self.secondary_muscles)))}")
        if self.equipment:
            parts.append(f":e:{'-'.join(map(str, sorted(self.equipment)))}")
        if self.tags:
            parts.append(f":t:{'-'.join(map(str, sorted(self.tags)))}")
        if self.category:
            parts.append(f":{self.category}")
        if self.difficulty_level:
            parts.append(f":{self.difficulty_level}")
        self._cache_key += "".join(parts)
