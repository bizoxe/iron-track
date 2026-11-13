import pytest
from pydantic import ValidationError

from app.domain.catalogs.schemas import EquipmentCreate


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("  ab  ", id="padding_does_not_satisfy_min_length"),
        pytest.param("ab", id="too_short"),
        pytest.param("a" * 101, id="too_long"),
    ],
)
def test_name_rejects_invalid_lengths(name: str) -> None:
    with pytest.raises(ValidationError):
        EquipmentCreate.model_validate({"name": name})


def test_name_non_string_fails_core_validation() -> None:
    """Core validation rejects non-strings passed through by the validator."""
    with pytest.raises(ValidationError):
        EquipmentCreate.model_validate({"name": 123})
