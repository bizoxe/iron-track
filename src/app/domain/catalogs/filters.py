from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import AfterValidator, Field, PrivateAttr

from app.lib.schema import CamelizedBaseSchema

if TYPE_CHECKING:
    from advanced_alchemy.filters import StatementFilter


class CatalogFilters(CamelizedBaseSchema):
    """Specific filters for Catalog domain."""

    search_string: Annotated[
        str | None,
        AfterValidator(lambda v: v.strip() if v else v),
        Field(max_length=50, description="Search term."),
    ] = None
    order_by: Annotated[Literal["id", "name"], Field(description="Field to order by.")] = "name"
    sort_order: Annotated[Literal["asc", "desc"], Field(description="Sort order ('asc' or 'desc').")] = "asc"

    _cache_key: str = PrivateAttr(default="")

    @property
    def as_aa_filters(self) -> list[StatementFilter]:
        """Filters including ordering and search."""
        filters: list[StatementFilter] = [
            aa_filters.OrderBy(field_name=self.order_by, sort_order=self.sort_order),
        ]

        if self.search_string:
            filters.append(aa_filters.SearchFilter(field_name="name", value=self.search_string, ignore_case=True))
        return filters

    def model_post_init(self, _context: Any) -> None:
        """Initialize the cache key on the provided filter values."""
        s = self.search_string.replace("\\", "\\\\").replace(":", "\\:") if self.search_string else "se:all"
        parts = [
            "CatF",
            f":{s}",
            f":{self.order_by}",
            f":{self.sort_order}",
        ]
        self._cache_key = "".join(parts)

    def __str__(self) -> str:
        """Return the cache key representation (not user-facing)."""
        return self._cache_key


class CatalogFiltersWithRetired(CatalogFilters):
    """Admin filters for Catalog domain.

    Extends the base catalog filters with an option to filter for retired
    (soft-deleted) catalog items.
    """

    show_only_retired: Annotated[
        bool,
        Field(description="Show only retired (soft-deleted) items."),
    ] = False

    @property
    def as_aa_filters(self) -> list[StatementFilter]:
        """Base filters with the retired-only criterion."""
        filters = super().as_aa_filters
        if self.show_only_retired:
            filters.append(aa_filters.ComparisonFilter(field_name="deleted_at", operator="ne", value=None))
        return filters
