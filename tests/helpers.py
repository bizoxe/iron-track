from __future__ import annotations

from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Any,
)

import anyio
from advanced_alchemy.utils.fixtures import open_fixture_async
from sqlalchemy import text
from sqlalchemy.dialects import postgresql as pg

from app.domain.catalogs.services import EquipmentService, ExerciseTagService, MuscleGroupService
from app.lib.jwt_utils import encode_jwt

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from uuid import UUID

    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncSession

type CatalogRegistryT = list[tuple[Sequence[dict[str, Any]], SQLAlchemyAsyncRepositoryService[Any, Any], list[str]]]


def add_role_to_raw_users(
    raw_users: list[dict[str, Any]],
    role_map: dict[str, UUID],
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
    key: str,
    timeout: float = 1.0,  # noqa: ASYNC109
    interval: float = 0.01,
) -> bool:
    """Wait for the specified key to appear in Redis until timeout.

    Used in tests to asynchronously verify the execution of FastAPI background tasks.

    Args:
        key: The Redis key to check for.
        timeout: The maximum time in seconds to wait for the key to appear.
        interval: The time in seconds to wait between checks.

    Returns:
        bool: True if the key is found before the timeout expires, False otherwise.
    """
    from cashews import cache

    end_time = anyio.current_time() + timeout

    while anyio.current_time() < end_time:
        if await cache.get(key) is not None:
            return True
        await anyio.sleep(interval)

    return False


def create_expired_access_token(
    user_id: UUID,
    email: str,
) -> str:
    """Create an expiring JWT access token."""
    jwt_payload = {
        "sub": str(user_id),
        "email": email,
    }

    return encode_jwt(
        payload=jwt_payload,
        expire_minutes=-1,
    )


def create_expired_refresh_token(user_id: UUID) -> str:
    """Create an expiring JWT refresh token."""
    jwt_payload = {
        "sub": str(user_id),
    }

    return encode_jwt(
        payload=jwt_payload,
        expire_timedelta=timedelta(minutes=-1),
    )


def prepare_enums(
    connection: Connection,
    enum_map: dict[Any, str],
) -> None:
    """Drop and recreate custom Postgres types."""
    for enum_class, type_name in enum_map.items():
        connection.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
        e = pg.ENUM(
            enum_class,
            name=type_name,
            values_callable=lambda cls: [member.value for member in cls],
        )
        e.create(connection)


async def seed_catalogs(
    fixtures_path: Path,
    session: AsyncSession,
) -> None:
    """Seed base catalog entities required for exercises.

    Must be executed before exercise seeding. Synchronizes PK sequences after insert.
    """
    muscle_groups_data = await open_fixture_async(fixtures_path, "muscle_groups")
    equipment_data = await open_fixture_async(fixtures_path, "equipment")
    tags_data = await open_fixture_async(fixtures_path, "exercise_tags")

    muscles_service = MuscleGroupService(session)
    equipment_service = EquipmentService(session)
    tags_service = ExerciseTagService(session)

    catalog_registry: CatalogRegistryT = [
        (muscle_groups_data, muscles_service, ["name"]),
        (equipment_data, equipment_service, ["name"]),
        (tags_data, tags_service, ["name"]),
    ]

    for data, svc, match in catalog_registry:
        await svc.upsert_many(data=data, match_fields=match, auto_commit=False)
        table_name = svc.model_type.__tablename__
        await session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "  # noqa: S608
                f"coalesce(max(id), 1)) FROM {table_name}"
            )
        )
