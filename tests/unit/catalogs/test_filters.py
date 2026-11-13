from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.catalogs.filters import CatalogFilters


def test_search_string_max_length_rejected() -> None:
    with pytest.raises(ValidationError):
        CatalogFilters.model_validate({"searchString": "a" * 51})


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
    assert CatalogFilters.model_validate(payload).search_string == expected


def test_cache_key_structure() -> None:
    filters = CatalogFilters.model_validate(
        {"searchString": "bench", "orderBy": "name", "sortOrder": "desc"},
    )
    assert str(filters) == "CatF:bench:name:desc"


def test_cache_key_empty_search_sentinel() -> None:
    assert str(CatalogFilters.model_validate({})) == "CatF:se:all:name:asc"


@pytest.mark.parametrize(
    ("search", "encoded"),
    [
        pytest.param("a:b", r"a\:b", id="colon"),
        pytest.param("se:all", r"se\:all", id="sentinel_lookalike"),
        pytest.param("back\\slash", r"back\\slash", id="backslash"),
    ],
)
def test_cache_key_escapes_search_term(search: str, encoded: str) -> None:
    key = str(CatalogFilters.model_validate({"searchString": search}))
    assert key == f"CatF:{encoded}:name:asc"
