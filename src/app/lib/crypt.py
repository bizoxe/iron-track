import os
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config.base import get_settings
from app.config.constants import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
)

settings = get_settings()

CRYPTO_MAX_WORKERS = settings.app.CRYPTO_MAX_WORKERS


def _get_default_crypto_workers() -> int:
    """Determine a safe default number of threads based on available CPU cores."""
    cores = os.cpu_count() or 1

    if hasattr(os, "sched_getaffinity"):
        with suppress(Exception):
            cores = len(os.sched_getaffinity(0))

    return max(min(cores, 4), 1)


final_workers = CRYPTO_MAX_WORKERS if CRYPTO_MAX_WORKERS is not None else _get_default_crypto_workers()

crypto_executor = ThreadPoolExecutor(
    max_workers=final_workers,
    thread_name_prefix="Argon2Pool",
)
"""Thread pool dedicated to cryptographic tasks."""

hasher = PasswordHash(
    (Argon2Hasher(time_cost=ARGON2_TIME_COST, memory_cost=ARGON2_MEMORY_COST, parallelism=ARGON2_PARALLELISM),)
)
"""The main password hashing interface, configured with Argon2id parameters."""


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
