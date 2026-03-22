from __future__ import annotations

from re import compile as re_compile
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import (
    Field,
    PrivateAttr,
)

from app.lib.schema import CamelizedBaseSchema

if TYPE_CHECKING:
    from advanced_alchemy.filters import StatementFilter


_CAMEL_TO_SNAKE_RE = re_compile(r"(?<!^)(?=[A-Z])")


class CommonFilters(CamelizedBaseSchema):
    """Base schema for standard API query parameters.

    Provides foundational support for pagination, ordering, and
    keyword-based searching across different domains.
    """

    search_string: Annotated[
        str | None,
        Field(description="Search term."),
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
    def aa_technical_filters(self) -> list[StatementFilter]:
        """Generate core SQLAlchemy filters for pagination, ordering, and search."""
        db_order_field = _CAMEL_TO_SNAKE_RE.sub("_", self.order_by).lower()
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

    def model_post_init(self, context: Any) -> None:
        """Initialize the unique cache key based on the provided filter values."""
        s = self.search_string.strip().replace(":", "|") if self.search_string else "se_all"
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
        return self._cache_key
