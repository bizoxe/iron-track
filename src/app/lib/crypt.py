from __future__ import annotations

import asyncio

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

hasher = PasswordHash((Argon2Hasher(),))


async def get_password_hash(
    password: str | bytes,
) -> str:
    """Get password hash.

    Args:
        password (str | bytes): Plaintext password.

    Returns:
        str: Hashed password.
    """
    return await asyncio.get_running_loop().run_in_executor(
        None,
        hasher.hash,
        password,
    )


async def verify_password(
    password: str | bytes,
    hashed_password: str,
) -> bool:
    """Verify password.

    Args:
        password (str | bytes): The string or bytes password.
        hashed_password (str): The hash of the password.

    Returns:
        bool: True if password matches hash.
    """
    valid, _ = await asyncio.get_running_loop().run_in_executor(
        None,
        hasher.verify_and_update,
        password,
        hashed_password,
    )

    return bool(valid)
