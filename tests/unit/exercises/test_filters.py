from typing import Any

import pytest

from app.domain.exercises.filters import ExerciseFilters


def test_cache_key_order_insensitive() -> None:
    a = ExerciseFilters.model_validate(
        {"primaryMuscles": [2, 1], "secondaryMuscles": [2, 1], "equipment": [2, 1], "tags": [2, 1]},
    )
    b = ExerciseFilters.model_validate(
        {"primaryMuscles": [1, 2], "secondaryMuscles": [1, 2], "equipment": [1, 2], "tags": [1, 2]},
    )
    assert str(a) == str(b)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        pytest.param({"primaryMuscles": [1]}, {"secondaryMuscles": [1]}, id="primary_vs_secondary"),
        pytest.param({"equipment": [1, 2]}, {"equipment": [1, 2], "tags": [3]}, id="tags_added"),
        pytest.param({"scope": "system"}, {"scope": "user"}, id="scope"),
        pytest.param({"category": "strength"}, {}, id="category_set_vs_unset"),
        pytest.param({"difficultyLevel": "beginner"}, {}, id="difficulty_set_vs_unset"),
    ],
)
def test_cache_key_distinguishes_filter_dimensions(a: dict[str, Any], b: dict[str, Any]) -> None:
    """Different filter dimensions never share a cache entry."""
    assert str(ExerciseFilters.model_validate(a)) != str(ExerciseFilters.model_validate(b))
