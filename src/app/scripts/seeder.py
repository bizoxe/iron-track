"""Seeds the system catalog: muscle groups, equipment, tags, system exercises.

Idempotent: tables are upserted on their natural keys within a single
transaction, so re-running is safe.

Standalone entrypoint: ``python -m app.scripts.seeder``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Sequence

    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
    from structlog.typing import FilteringBoundLogger


async def seed_db(logger: FilteringBoundLogger) -> None:
    """Populate the database with system-default fixture data."""
    # Runtime imports stay local: importing this module doesn't pull the app
    # graph — only seed_db() pays for it.
    from contextlib import aclosing
    from pathlib import Path

    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from app.config.app_settings import sqlalchemy_config
    from app.config.base import get_settings
    from app.domain.catalogs.deps import (
        provide_equipment_service,
        provide_muscle_groups_service,
        provide_tags_service,
    )
    from app.domain.exercises.deps import provide_exercises_service

    async def get_service[T](gen: AsyncGenerator[T, None]) -> T:
        """Helper to safely consume and close a service generator."""
        async with aclosing(gen) as g:
            return await anext(g)

    async def reset_sequence(service: SQLAlchemyAsyncRepositoryService[Any, Any]) -> None:
        """Reset the Postgres primary key sequence to the current maximum ID."""
        table_name = service.model_type.__tablename__
        await service.repository.session.execute(
            text(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), coalesce(max(id), 1)) FROM {table_name}")
        )

    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    muscle_groups = await open_fixture_async(fixtures_path, "muscle_groups")
    equipment = await open_fixture_async(fixtures_path, "equipment")
    system_exercises = await open_fixture_async(fixtures_path, "system_exercises")
    exercise_tags = await open_fixture_async(fixtures_path, "exercise_tags")

    async with sqlalchemy_config.get_session() as session:
        try:
            await session.execute(text("SELECT 1"))
        except (OSError, DBAPIError):
            logger.error("Database connection failed")
            raise

        muscle_groups_service = await get_service(provide_muscle_groups_service(session))
        equipment_service = await get_service(provide_equipment_service(session))
        tags_service = await get_service(provide_tags_service(session))
        exercises_service = await get_service(provide_exercises_service(session))

        services_registry: list[
            tuple[Sequence[dict[str, Any]], SQLAlchemyAsyncRepositoryService[Any, Any], list[str], bool]
        ] = [
            (muscle_groups, muscle_groups_service, ["name"], True),
            (equipment, equipment_service, ["name"], True),
            (exercise_tags, tags_service, ["name"], True),
            (system_exercises, exercises_service, ["slug"], False),
        ]

        for data, svc, match, needs_sequence_reset in services_registry:
            try:
                logger.info(
                    "Preparing to seed data...",
                    table=svc.model_type.__tablename__,
                    count=len(data),
                )
                await svc.upsert_many(data=data, match_fields=match, auto_commit=False)
                if needs_sequence_reset:
                    await reset_sequence(svc)
            except Exception:
                logger.error("Seeding aborted", table=svc.model_type.__tablename__)
                raise
        await session.commit()


if __name__ == "__main__":
    import sys

    import anyio
    from structlog import get_logger

    st_logger = get_logger()
    st_logger.info("Starting database seeding...")

    try:
        anyio.run(seed_db, st_logger)
        st_logger.info("Database seeding complete...")
    except Exception:
        st_logger.exception("Seeding failed")
        sys.exit(1)
