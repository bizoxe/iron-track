from __future__ import annotations

from re import compile as re_compile
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Literal,
)

from advanced_alchemy.extensions.fastapi import filters as aa_filters
from pydantic import Field

from app.lib.schema import CamelizedBaseSchema

if TYPE_CHECKING:
    from advanced_alchemy.filters import StatementFilter


_CAMEL_TO_SNAKE_RE = re_compile(r"(?<!^)(?=[A-Z])")


class CommonFilters(CamelizedBaseSchema):
    """Base requirements for pagination, ordering, and keyword search."""

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
        Field(ge=1, description="Number of items per page."),
    ] = 20
    order_by: Annotated[
        str,
        Field(description="Field to order by."),
    ] = "name"
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(description="Sort order ('asc' or 'desc')."),
    ] = "asc"

    @property
    def aa_technical_filters(self) -> list[StatementFilter]:
        """Technical filters including pagination, ordering, and search."""
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
