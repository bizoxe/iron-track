from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import AwareDatetime, Field

from app.lib.filters import CommonFilters

if TYPE_CHECKING:
    from advanced_alchemy.filters import StatementFilter


class UserFilters(CommonFilters):
    """Specific filters for User domain."""

    search_fields: ClassVar[set[str]] = {"name", "email"}
    order_by: Annotated[
        Literal["name", "email", "createdAt"],
        Field(description="Field to order by."),
    ] = "name"
    is_active: Annotated[
        bool | None,
        Field(description="Filter by active or inactive status."),
    ] = None
    created_before: Annotated[
        AwareDatetime | None,
        Field(description="Filter by created date before this timestamp (ISO 8601 UTC). Example: 2026-03-10T14:00:00Z"),
    ] = None
    created_after: Annotated[
        AwareDatetime | None,
        Field(description="Filter by created date after this timestamp (ISO 8601 UTC). Example: 2026-03-10T14:00:00Z"),
    ] = None

    @property
    def aa_technical_filters(self) -> list[StatementFilter]:
        """Extend base filters with user-specific criteria."""
        filters = super().aa_technical_filters

        if self.created_after or self.created_before:
            filters.append(
                aa_filters.OnBeforeAfter(
                    field_name="created_at",
                    on_or_before=self.created_before,
                    on_or_after=self.created_after,
                )
            )
        if self.is_active is not None:
            filters.append(aa_filters.CollectionFilter(field_name="is_active", values=[self.is_active]))

        return filters

    def model_post_init(self, context: Any) -> None:
        """Extend the base cache key with user-specific filter parameters."""
        super().model_post_init(context)
        parts = []
        if self.is_active is not None:
            parts.append(f":{self.is_active}")
        if self.created_before:
            parts.append(f":{self.created_before}")
        if self.created_after:
            parts.append(f":{self.created_after}")
        self._cache_key += "".join(parts)
