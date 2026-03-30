from __future__ import annotations

from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
)
from uuid import UUID

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import Field
from sqlalchemy import or_

from app.db import models as m
from app.domain.exercises.schemas import (
    CategoryType,
    DifficultyLevelType,
    ExerciseScope,
)
from app.lib.filters import CommonFilters

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


type ScopeStrategyT = Mapping[ExerciseScope, Callable[[UUID | None], aa_filters.StatementFilter]]

_SCOPE_STRATEGY: ScopeStrategyT = MappingProxyType(
    {
        ExerciseScope.SYSTEM: lambda _: aa_filters.ComparisonFilter("created_by", "eq", None),
        ExerciseScope.USER: lambda uid: aa_filters.ComparisonFilter("created_by", "eq", uid),
        ExerciseScope.ALL: lambda uid: aa_filters.FilterGroup(
            logical_operator=or_,
            filters=[
                aa_filters.ComparisonFilter("created_by", "eq", None),
                aa_filters.ComparisonFilter("created_by", "eq", uid),
            ],
        ),
    }
)


class ExerciseFilters(CommonFilters):
    """Specific filters for Exercise domain."""

    scope: Annotated[
        ExerciseScope,
        Field(description="Data ownership scope (system/user/all)."),
    ] = ExerciseScope.ALL
    primary_muscles: Annotated[
        list[int] | None,
        Field(description="Target muscle group IDs."),
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
        CategoryType | None,
        Field(description="Exercise categories."),
    ] = None
    difficulty_level: Annotated[
        DifficultyLevelType | None,
        Field(description="Experience levels."),
    ] = None

    def build_exercise_filters(
        self,
        user_id: UUID,
    ) -> list[aa_filters.StatementFilter]:
        """Transform filter attributes into Advanced Alchemy statement criteria.

        Args:
            user_id: The ID of the user requesting the exercises for scope filtering.

        Returns:
            list[StatementFilter]: A list of filters.
        """
        filters = [_SCOPE_STRATEGY[self.scope](user_id), *self.aa_technical_filters]
        if self.primary_muscles:
            filters.append(
                aa_filters.ExistsFilter(
                    values=[
                        m.exercise_primary_muscles.c.exercise_id == m.Exercise.id,
                        m.exercise_primary_muscles.c.muscle_group_id.in_(self.primary_muscles),
                    ]
                )
            )

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
                        m.exercise_tag_map.c.exercise_id == m.Exercise.id,
                        m.exercise_tag_map.c.tag_id.in_(self.tags),
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

    def model_post_init(self, context: Any) -> None:
        """Extend the base cache key with exercise-specific filter parameters."""
        super().model_post_init(context)
        parts = [f":{self.scope}"]
        if self.primary_muscles:
            parts.append(f":{'-'.join(map(str, sorted(self.primary_muscles)))}")
        if self.equipment:
            parts.append(f":{'-'.join(map(str, sorted(self.equipment)))}")
        if self.tags:
            parts.append(f":{'-'.join(map(str, sorted(self.tags)))}")
        if self.category:
            parts.append(f":{self.category}")
        if self.difficulty_level:
            parts.append(f":{self.difficulty_level}")
        self._cache_key += "".join(parts)
