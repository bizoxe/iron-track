from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    Self,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import Field, model_validator
from sqlalchemy import and_

from app.lib.filters import CommonFilters, CreatedAtRangeFilters

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import StatementFilter


class UserFilters(CreatedAtRangeFilters, CommonFilters):
    """Specific admin filters for Account domain."""

    search_fields: ClassVar[set[str]] = {"name", "email"}
    order_by: Annotated[
        Literal["name", "email", "createdAt"],
        Field(description="Field to order by."),
    ] = "name"
    show_only_banned: Annotated[
        bool,
        Field(description="Show only administratively banned accounts."),
    ] = False
    show_only_retired: Annotated[
        bool,
        Field(description="Show only retired (soft-deleted) accounts."),
    ] = False

    @model_validator(mode="after")
    def check_status_flags_not_combined(self) -> Self:
        if self.show_only_banned and self.show_only_retired:
            msg = "Cannot filter by banned and retired accounts simultaneously. Select only one status"
            raise ValueError(msg)
        return self

    @property
    def as_aa_filters(self) -> list[StatementFilter]:
        """Base filters with user-specific criteria."""
        filters = super().as_aa_filters
        if self.show_only_banned:
            filters.append(
                aa_filters.FilterGroup(
                    logical_operator=and_,
                    filters=[
                        aa_filters.ComparisonFilter(field_name="is_active", operator="eq", value=False),
                        aa_filters.ComparisonFilter(field_name="deleted_at", operator="eq", value=None),
                    ],
                )
            )
        if self.show_only_retired:
            filters.append(aa_filters.ComparisonFilter(field_name="deleted_at", operator="ne", value=None))
        if self.range_filter is not None:
            filters.append(self.range_filter)

        return filters

    def model_post_init(self, context: Any) -> None:
        """Extend the base cache key with user-specific filter parameters."""
        super().model_post_init(context)
        parts = []
        if self.show_only_banned:
            parts.append(":banned")
        if self.show_only_retired:
            parts.append(":retired")
        if self.created_before:
            parts.append(f":cb:{self.created_before}")
        if self.created_after:
            parts.append(f":ca:{self.created_after}")
        self._cache_key += "".join(parts)


class UserExerciseFilters(CreatedAtRangeFilters, CommonFilters):
    """Admin filters for a user's exercises."""

    # Uncached by design: low query frequency and small per-user dataset
    # do not justify caching overhead.

    order_by: Annotated[
        Literal["name", "createdAt"],
        Field(description="Field to order by."),
    ] = "name"

    def build_user_exercise_filters(self, user_id: UUID) -> list[StatementFilter]:
        """Build statement filters for a user's exercises."""
        filters: list[StatementFilter] = [
            *self.as_aa_filters,
            aa_filters.ComparisonFilter(field_name="created_by", operator="eq", value=user_id),
        ]
        if self.range_filter is not None:
            filters.append(self.range_filter)

        return filters
