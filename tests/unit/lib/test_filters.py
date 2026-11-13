from datetime import timedelta
from typing import Any

import pytest
from advanced_alchemy import filters as aa_filters
from pydantic import ValidationError

from app.lib.filters import (
    CommonFilters,
    CreatedAtRangeFilters,
    camel_to_snake,
)

# --- camel_to_snake ---


@pytest.mark.parametrize(
    ("camel", "snake"),
    [
        pytest.param("name", "name", id="single_word"),
        pytest.param("createdAt", "created_at", id="multi_segment"),
    ],
)
def test_camel_to_snake(camel: str, snake: str) -> None:
    assert camel_to_snake(camel) == snake


# --- Search and Pagination Declarations ---


def test_search_string_max_length_rejected() -> None:
    with pytest.raises(ValidationError):
        CommonFilters.model_validate({"searchString": "a" * 101})


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param({}, None, id="absent"),
        pytest.param({"searchString": None}, None, id="explicit_none"),
        pytest.param({"searchString": "   "}, "", id="whitespace_only"),
        pytest.param({"searchString": "  bench  "}, "bench", id="padded"),
    ],
)
def test_search_string_normalization(payload: dict[str, Any], expected: str | None) -> None:
    assert CommonFilters.model_validate(payload).search_string == expected


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"currentPage": 0}, id="page_below_one"),
        pytest.param({"pageSize": 0}, id="size_below_one"),
        pytest.param({"pageSize": 101}, id="size_above_hundred"),
    ],
)
def test_pagination_bounds_rejected(payload: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        CommonFilters.model_validate(payload)


# --- Cache Key ---


def test_cache_key_structure() -> None:
    filters = CommonFilters.model_validate(
        {"searchString": "bench", "currentPage": 2, "pageSize": 10, "orderBy": "name", "sortOrder": "desc"},
    )
    assert str(filters) == "CF:bench:2:10:name:desc"


def test_cache_key_empty_search_sentinel() -> None:
    filters = CommonFilters.model_validate({})
    assert str(filters) == "CF:se:all:1:20:name:asc"


@pytest.mark.parametrize(
    ("search", "encoded"),
    [
        pytest.param("a:b", r"a\:b", id="colon"),
        pytest.param("se:all", r"se\:all", id="sentinel_lookalike"),
        pytest.param("back\\slash", r"back\\slash", id="backslash"),
    ],
)
def test_cache_key_escapes_search_term(search: str, encoded: str) -> None:
    key = str(CommonFilters.model_validate({"searchString": search}))
    assert key == f"CF:{encoded}:1:20:name:asc"


# --- Created Range ---


@pytest.mark.parametrize("field", ["createdBefore", "createdAfter"])
def test_created_range_requires_timezone(field: str) -> None:
    """Both range fields declare AwareDatetime: naive timestamps are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CreatedAtRangeFilters.model_validate({field: "2027-01-01T00:00:00"})
    error_fields = {err["loc"][-1] for err in exc_info.value.errors()}
    assert error_fields == {field}


@pytest.mark.parametrize(
    ("payload", "expect_filter"),
    [
        pytest.param({}, False, id="no_bounds"),
        pytest.param({"createdAfter": "2030-01-01T00:00:00Z"}, True, id="after_only"),
        pytest.param({"createdBefore": "2020-01-01T00:00:00Z"}, True, id="before_only"),
        pytest.param(
            {"createdBefore": "2020-01-01T00:00:00Z", "createdAfter": "2019-01-01T00:00:00Z"},
            True,
            id="both_bounds",
        ),
    ],
)
def test_range_filter_assembly(payload: dict[str, str], expect_filter: bool) -> None:
    filters = CreatedAtRangeFilters.model_validate(payload)
    assembled = filters.range_filter
    if not expect_filter:
        assert assembled is None
        return
    assert isinstance(assembled, aa_filters.OnBeforeAfter)
    assert assembled.on_or_before == filters.created_before
    assert assembled.on_or_after == filters.created_after


@pytest.mark.parametrize("field", ["createdBefore", "createdAfter"])
def test_created_range_null_bounds_stay_none(field: str) -> None:
    filters = CreatedAtRangeFilters.model_validate({field: None})
    assert filters.created_before is None
    assert filters.created_after is None


@pytest.mark.parametrize("field", ["createdBefore", "createdAfter"])
def test_created_range_normalized_to_utc(field: str) -> None:
    """Range bounds are stored in UTC regardless of the input offset."""
    filters = CreatedAtRangeFilters.model_validate({field: "2030-01-01T02:00:00+02:00"})
    normalized = getattr(filters, camel_to_snake(field))
    assert normalized is not None
    assert normalized.utcoffset() == timedelta(0)
