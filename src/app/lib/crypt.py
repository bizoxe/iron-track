from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config.base import get_settings
from app.config.constants import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
)

crypto_executor = ThreadPoolExecutor(
    max_workers=get_settings().app.crypto_workers,
    thread_name_prefix="Argon2Pool",
)

hasher = PasswordHash(
    (Argon2Hasher(time_cost=ARGON2_TIME_COST, memory_cost=ARGON2_MEMORY_COST, parallelism=ARGON2_PARALLELISM),)
)


async def get_password_hash(password: str | bytes) -> str:
    """Get password hash.

    Args:
        password (str | bytes): Plain password.

    Returns:
        str: Hashed password.
    """
    return await get_running_loop().run_in_executor(crypto_executor, hasher.hash, password)


async def verify_password(plain_password: str | bytes, hashed_password: str) -> bool:
    """Verify Password.

    Args:
        plain_password (str | bytes): The string or byte password.
        hashed_password (str): The hash of the password.

    Returns:
        bool: True if password matches hash.
    """
    valid, _ = await get_running_loop().run_in_executor(
        crypto_executor,
        hasher.verify_and_update,
        plain_password,
        hashed_password,
    )
    return bool(valid)
