import pytest
from pydantic import ValidationError

from app.domain.accounts.filters import UserFilters


def test_status_flags_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError, match="Cannot filter by banned and retired"):
        UserFilters.model_validate({"showOnlyBanned": True, "showOnlyRetired": True})


def test_cache_key_admin_flags_and_ranges() -> None:
    base = str(UserFilters.model_validate({}))
    assert str(UserFilters.model_validate({"showOnlyBanned": True})) == f"{base}:banned"
    assert str(UserFilters.model_validate({"showOnlyRetired": True})) == f"{base}:retired"
    assert str(UserFilters.model_validate({"createdBefore": "2030-01-01T00:00:00Z"})) == (
        f"{base}:cb:2030-01-01 00:00:00+00:00"
    )
    assert str(UserFilters.model_validate({"createdAfter": "2030-01-01T00:00:00Z"})) == (
        f"{base}:ca:2030-01-01 00:00:00+00:00"
    )
