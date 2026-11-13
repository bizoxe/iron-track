from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.utils.fixtures import open_fixture_async
from sqlalchemy import text

from app.db.enums import drop_enum_types_ddl, iter_enum_type_ddl
from app.domain.accounts.jwt_helpers import create_access_token
from app.domain.catalogs.services import (
    EquipmentService,
    MuscleGroupService,
    TagService,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from uuid import UUID

    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from httpx2 import AsyncClient
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import AsyncSession


def add_role_to_raw_users(
    raw_users: list[dict[str, Any]],
    role_map: dict[str, UUID],
) -> list[dict[str, Any]]:
    for user in raw_users:
        role_slug = user.pop("role_slug")
        user["role_id"] = role_map[role_slug]

    return raw_users


def recreate_enum_types(sync_conn: Connection) -> None:
    """Drop and recreate PostgreSQL enum types."""
    sync_conn.execute(text(drop_enum_types_ddl()))
    for stmt in iter_enum_type_ddl():
        sync_conn.execute(text(stmt))


async def seed_catalogs(fixtures_path: Path, session: AsyncSession) -> None:
    """Seed base catalog entities required for exercises.

    Must be executed before exercise seeding. Synchronizes PK sequences after insert.
    """
    muscle_groups = await open_fixture_async(fixtures_path, "muscle_groups")
    equipment = await open_fixture_async(fixtures_path, "equipment")
    tags = await open_fixture_async(fixtures_path, "exercise_tags")

    muscle_groups_service = MuscleGroupService(session)
    equipment_service = EquipmentService(session)
    tags_service = TagService(session)

    catalog_registry: list[tuple[Sequence[dict[str, Any]], SQLAlchemyAsyncRepositoryService[Any, Any], list[str]]] = [
        (muscle_groups, muscle_groups_service, ["name"]),
        (equipment, equipment_service, ["name"]),
        (tags, tags_service, ["name"]),
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


def set_access_cookie(
    client: AsyncClient,
    user_id: UUID,
    email: str,
) -> str:
    token = create_access_token(user_id=user_id, email=email)
    client.cookies.set(name="access_token", value=token)
    return token
