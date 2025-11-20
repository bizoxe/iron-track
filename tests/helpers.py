from typing import (
    TYPE_CHECKING,
    Any,
)

import anyio

if TYPE_CHECKING:
    from uuid import UUID

    from redis.asyncio import Redis


def add_role_to_raw_users(
    raw_users: list[dict[str, Any]],
    role_map: dict[str, "UUID"],
) -> list[dict[str, Any]]:
    default_role_id = role_map["Application Access"]
    super_role_id = role_map["Superuser"]
    trainer_role_id = role_map["Fitness Trainer"]

    for user in raw_users:
        user_name = user.get("name", "")
        if user_name.startswith(("System", "Super")):
            user["role_id"] = super_role_id
        elif user_name.startswith("Fitness"):
            user["role_id"] = trainer_role_id
        else:
            user["role_id"] = default_role_id

    return raw_users


async def wait_for_blacklist_entry(
    redis_client: "Redis",
    key: str,
    timeout: float = 1.0,  # noqa: ASYNC109
    interval: float = 0.01,
) -> bool:
    """Wait for the specified key to appear in Redis until timeout.

    Used in tests to asynchronously verify the execution of FastAPI background tasks.

    Args:
        redis_client: The Redis client instance.
        key: The Redis key to check for.
        timeout: The maximum time in seconds to wait for the key to appear.
        interval: The time in seconds to wait between checks.

    Returns:
        True if the key is found before the timeout expires, False otherwise.
    """
    end_time = anyio.current_time() + timeout

    while anyio.current_time() < end_time:
        if await redis_client.get(key) is not None:
            return True
        await anyio.sleep(interval)

    return False
