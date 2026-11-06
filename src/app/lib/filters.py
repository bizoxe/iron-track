from __future__ import annotations

from datetime import UTC
from re import compile as re_compile
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import AfterValidator, AwareDatetime, Field, PrivateAttr

from app.lib.schema import CamelizedBaseSchema

if TYPE_CHECKING:
    from advanced_alchemy.filters import StatementFilter


_CAMEL_TO_SNAKE_RE = re_compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(field: str) -> str:
    """Convert a camelCase query field name to its snake_case column name."""
    return _CAMEL_TO_SNAKE_RE.sub("_", field).lower()


class CommonFilters(CamelizedBaseSchema):
    """Base schema for standard API query parameters.

    Provides foundational support for pagination, ordering, and
    keyword-based searching across different domains.
    """

    search_string: Annotated[
        str | None,
        AfterValidator(lambda v: v.strip() if v else v),
        Field(max_length=100, description="Search term."),
    ] = None
    search_fields: ClassVar[str | set[str]] = "name"
    current_page: Annotated[
        int,
        Field(ge=1, description="Page number for pagination."),
    ] = 1
    page_size: Annotated[
        int,
        Field(ge=1, le=100, description="Number of items per page."),
    ] = 20
    order_by: Annotated[
        str,
        Field(description="Field to order by."),
    ] = "name"
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(description="Sort order ('asc' or 'desc')."),
    ] = "asc"

    _cache_key: str = PrivateAttr(default="")

    @property
    def as_aa_filters(self) -> list[StatementFilter]:
        """Core filters for pagination, ordering, and search."""
        db_order_field = camel_to_snake(field=self.order_by)
        filters: list[StatementFilter] = [
            aa_filters.LimitOffset(
                limit=self.page_size,
                offset=self.page_size * (self.current_page - 1),
            ),
            aa_filters.OrderBy(field_name=db_order_field, sort_order=self.sort_order),
        ]

        if self.search_string:
            filters.append(
                aa_filters.SearchFilter(field_name=self.search_fields, value=self.search_string, ignore_case=True)
            )
        return filters

    def model_post_init(self, _context: Any) -> None:
        """Initialize the unique cache key based on the provided filter values."""
        s = self.search_string.replace("\\", "\\\\").replace(":", "\\:") if self.search_string else "se:all"
        parts = [
            "CF",
            f":{s}",
            f":{self.current_page}",
            f":{self.page_size}",
            f":{self.order_by}",
            f":{self.sort_order}",
        ]
        self._cache_key = "".join(parts)

    def __str__(self) -> str:
        """Return the cache key representation (not user-facing)."""
        return self._cache_key


class CreatedAtRangeFilters(CamelizedBaseSchema):
    """Created-at range filters with inclusive bounds."""

    range_field_name: ClassVar[str] = "created_at"
    created_before: Annotated[
        AwareDatetime | None,
        AfterValidator(lambda v: v.astimezone(UTC) if v else v),
        Field(
            description=(
                "Filter by created date on or before this timestamp (ISO 8601 UTC). Example: 2026-03-10T14:00:00Z"
            ),
        ),
    ] = None
    created_after: Annotated[
        AwareDatetime | None,
        AfterValidator(lambda v: v.astimezone(UTC) if v else v),
        Field(
            description=(
                "Filter by created date on or after this timestamp (ISO 8601 UTC). Example: 2026-03-10T14:00:00Z"
            ),
        ),
    ] = None

    @property
    def range_filter(self) -> StatementFilter | None:
        """Created-at range criterion."""
        if self.created_before is None and self.created_after is None:
            return None
        return aa_filters.OnBeforeAfter(
            field_name=self.range_field_name,
            on_or_before=self.created_before,
            on_or_after=self.created_after,
        )
