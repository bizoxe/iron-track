import pytest

from app.lib import crypt

pytestmark = pytest.mark.anyio


async def test_get_password_hash() -> None:
    """Test that the encryption key is formatted correctly."""
    secret_str = "This is a password!"  # noqa: S105
    secret_bytes = b"This is a password too!"
    secret_str_hash = await crypt.get_password_hash(secret_str)
    secret_bytes_hash = await crypt.get_password_hash(secret_bytes)

    assert secret_str_hash.startswith("$argon2")
    assert secret_bytes_hash.startswith("$argon2")


@pytest.mark.parametrize(
    ("valid_password", "tested_password", "expected_result"),
    [
        ("SuperS3cret123456789!!", "SuperS3cret123456789!!", True),
        ("SuperS3cret123456789!!", "Invalid!!", False),
    ],
)
async def test_verify_password(valid_password: str, tested_password: str, expected_result: bool) -> None:
    """Test that the encryption key is formatted correctly."""
    secret_str_hash = await crypt.get_password_hash(valid_password)
    is_valid = await crypt.verify_password(tested_password, secret_str_hash)

    assert is_valid == expected_result
