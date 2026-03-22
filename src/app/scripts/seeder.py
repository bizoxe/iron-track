from __future__ import annotations

from typing import Any


async def seed_db(logger: Any) -> None:
    """Populate the database with system-default fixture data."""
    from pathlib import Path
    from typing import TYPE_CHECKING

    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import text

    from app.config.app_settings import sqlalchemy_config
    from app.config.base import get_settings
    from app.domain.catalogs.deps import (
        provide_equipment_service,
        provide_exercise_tag_service,
        provide_muscle_group_service,
    )
    from app.domain.exercises.deps import provide_exercise_service
    from app.server.lifespan import setup_app_cache

    if TYPE_CHECKING:
        from collections.abc import Sequence

        from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

    type CatalogMapT = list[tuple[Sequence[dict[str, Any]], SQLAlchemyAsyncRepositoryService[Any, Any], list[str]]]

    async def _seed_db() -> None:
        settings = get_settings()
        setup_app_cache(settings=settings)
        fixtures_path = Path(settings.db.FIXTURE_PATH)
        muscle_groups_data = await open_fixture_async(fixtures_path, "muscle_groups")
        equipment_data = await open_fixture_async(fixtures_path, "equipment")
        exercises_data = await open_fixture_async(fixtures_path, "all_exercises")
        tags_data = await open_fixture_async(fixtures_path, "exercise_tags")

        async def reset_sequence(service: SQLAlchemyAsyncRepositoryService[Any, Any]) -> None:
            """Reset the Postgres primary key sequence to the current maximum ID."""
            table_name = service.model_type.__tablename__
            await service.repository.session.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "  # noqa: S608
                    f"coalesce(max(id), 1)) FROM {table_name}"
                )
            )

        async with sqlalchemy_config.get_session() as session:
            try:
                await session.execute(text("SELECT 1"))
            except OSError:
                await logger.aerror("Database connection failed")
                raise

            muscles_service = await anext(provide_muscle_group_service(session))
            equipment_service = await anext(provide_equipment_service(session))
            tags_service = await anext(provide_exercise_tag_service(session))
            exercise_service = await anext(provide_exercise_service(session))

            catalog_map: CatalogMapT = [
                (muscle_groups_data, muscles_service, ["name"]),
                (equipment_data, equipment_service, ["name"]),
                (tags_data, tags_service, ["name"]),
                (exercises_data, exercise_service, ["name"]),
            ]

            for data, svc, match in catalog_map:
                try:
                    await logger.ainfo(
                        "Preparing to seed data...",
                        table=svc.model_type.__tablename__,
                        count=len(data),
                    )
                    await svc.upsert_many(data=data, match_fields=match, auto_commit=False)
                    if svc.model_type.__tablename__ != exercise_service.model_type.__tablename__:
                        await reset_sequence(svc)
                except Exception:
                    await logger.aexception("Seeding aborted", table=svc.model_type.__tablename__)
                    raise
            await session.commit()

    await _seed_db()


if __name__ == "__main__":
    import sys

    import anyio
    from structlog import get_logger

    st_logger = get_logger()
    st_logger.info("Starting database seeding...")

    try:
        anyio.run(seed_db, st_logger)
        st_logger.info("Database seeding complete...")
    except (Exception, OSError):  # noqa: BLE001
        sys.exit(1)
