from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.utils.fixtures import open_fixture_async
from cashews import cache as cashews_cache
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.app_settings import sqlalchemy_config
from app.config.base import get_settings
from app.domain.accounts.jwt_helpers import (
    create_access_token,
    create_refresh_token,
)
from app.domain.accounts.services import RoleService, UserService
from app.domain.exercises.services import ExerciseService
from app.lib.serializers import MsgSpecRegistry
from tests import constants
from tests.helpers import (
    add_role_to_raw_users,
    recreate_enum_types,
    seed_catalogs,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from uuid import UUID

    from fastapi import FastAPI
    from pytest_databases.docker.postgres import PostgresService
    from pytest_databases.docker.valkey import ValkeyService
    from pytest_mock import MockerFixture
    from sqlalchemy.ext.asyncio import AsyncEngine

project_dir = Path(__file__).resolve().parents[2]

# --- Database and session ---


@pytest.fixture(scope="session", name="engine")
async def fx_engine(postgres_service: PostgresService) -> AsyncEngine:
    """PostgreSQL instance for end-to-end testing."""
    return create_async_engine(
        URL(
            drivername="postgresql+asyncpg",
            username=postgres_service.user,
            password=postgres_service.password,
            host=postgres_service.host,
            port=postgres_service.port,
            database=postgres_service.database,
            query={},  # type: ignore[arg-type]
        ),
        echo=False,
    )


@pytest.fixture(scope="session", name="setup_db_schema")
async def fx_setup_database_schema(engine: AsyncEngine) -> None:
    metadata = orm_registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(recreate_enum_types)
        await conn.run_sync(metadata.create_all)


@pytest.fixture(scope="session", name="sessionmaker")
def fx_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="session")
async def fx_session(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        session = sessionmaker(bind=conn)
        try:
            yield session
        finally:
            await conn.rollback()
            await session.close()


# --- Reference seeding ---


@pytest.fixture(scope="session", name="seed_roles")
async def fx_seed_roles(
    setup_db_schema: None,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> dict[str, UUID]:
    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with sessionmaker() as session:
        roles_service = RoleService(session)
        fixture = await open_fixture_async(fixtures_path, "role")
        roles_obj = await roles_service.upsert_many(match_fields=["name"], data=fixture, auto_commit=True)
        return {role.slug: role.id for role in roles_obj}


@pytest.fixture(scope="session", name="seed_catalogs_and_exercises")
async def fx_seed_catalogs_and_exercises(
    setup_db_schema: None,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    fixtures_path = project_dir / "tests" / "fixtures"
    system_exercises = await open_fixture_async(fixtures_path, "system_exercises")
    async with sessionmaker() as session:
        await seed_catalogs(fixtures_path=fixtures_path, session=session)
        exercises_service = ExerciseService(session)
        await exercises_service.upsert_many(data=system_exercises, match_fields=["slug"], auto_commit=False)
        await session.commit()


# --- Test infrastructure (autouse, never requested directly) ---


@pytest.fixture(autouse=True)
async def _prepare_db(
    seed_roles: dict[str, UUID],
    seed_catalogs_and_exercises: None,
    session: AsyncSession,
    raw_users: list[dict[str, Any]],
    exercise_samples: list[dict[str, Any]],
) -> None:
    users_to_create = deepcopy(raw_users)
    users_service = UserService(session)
    raw_users_with_roles = add_role_to_raw_users(
        raw_users=users_to_create,
        role_map=seed_roles,
    )
    await users_service.create_many(raw_users_with_roles, auto_commit=False)
    exercises_to_create = deepcopy(exercise_samples)
    exercises_service = ExerciseService(session)
    await exercises_service.create_many(data=exercises_to_create, auto_commit=False)
    await session.flush()


@pytest.fixture(autouse=True)
def _patch_db(
    app: FastAPI,
    engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
    session: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """Configure the application's database access for transactional testing.

    This fixture patches the Advanced-Alchemy configuration and substitutes the
    session maker to ensure all HTTP requests run within a single, test-managed
    transaction that is rolled back upon completion. This approach maintains the
    integrity of the ORM's exception translation mechanism.

    This fixture has the following side effects:

    1. Mocker Patches (Session Object): The `commit()`, `rollback()`, and `close()`
       methods are temporarily mocked as AsyncMocks directly on the session object.
       This prevents the Advanced-Alchemy management logic from prematurely
       terminating the fixture's transaction.

    2. Advanced-Alchemy Configuration: The engine instance is set to the test
       PostgreSQL Engine. The session_maker is replaced with a function
       (lambda: session) that returns the real AsyncSession object bound to the
       test transaction.
    """
    mocker.patch.object(session, "commit", new_callable=mocker.AsyncMock)
    mocker.patch.object(session, "rollback", new_callable=mocker.AsyncMock)
    mocker.patch.object(session, "close", new_callable=mocker.AsyncMock)

    monkeypatch.setattr(sqlalchemy_config, "engine_instance", engine)
    monkeypatch.setattr(sqlalchemy_config, "session_maker", lambda: session)


@pytest.fixture(scope="session", autouse=True)
def _setup_cashews(valkey_service: ValkeyService) -> None:
    test_redis_url = f"redis://{valkey_service.host}:{valkey_service.port}/{valkey_service.db}"
    # ASGITransport does not run the app lifespan, so the cache setup from
    # setup_app_cache() (registration + pickle_type) must be mirrored here
    # (client_side/suppress are intentionally test-specific).
    MsgSpecRegistry.register_in_cashews()
    cashews_cache.setup(
        settings_url=test_redis_url,
        client_side=False,  # every read is a real GET through the serializer
        suppress=False,  # raise on backend errors instead of turning them into silent cache misses
        socket_timeout=0.5,
        pickle_type="null",
    )


@pytest.fixture(autouse=True)
async def _clear_cache() -> AsyncGenerator[None, None]:
    await cashews_cache.clear()
    yield


# --- HTTP clients ---
# httpx2: cookies set programmatically by the fixtures carry no domain/path
# attributes, so a server-side delete_cookie (deletion header with Path=/)
# never evicts them from the client jar. After a route clears its cookies,
# assert response.cookies only — never the client jar.


@pytest.fixture(name="client")
async def fx_client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(name="superuser_client")
async def fx_superuser_client_set_cookie(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        access_token = create_access_token(
            user_id=constants.SUPERUSER_ID,
            email=constants.SUPERUSER_EMAIL,
        )
        refresh_token = create_refresh_token(user_id=constants.SUPERUSER_ID)
        client.cookies.set(name="access_token", value=access_token)
        client.cookies.set(name="refresh_token", value=refresh_token)

        yield client


@pytest.fixture(name="user_client")
def fx_user_client_set_cookie(client: AsyncClient) -> AsyncClient:
    access_token = create_access_token(
        user_id=constants.USER_EXAMPLE_ID,
        email=constants.USER_EXAMPLE_EMAIL,
    )
    refresh_token = create_refresh_token(user_id=constants.USER_EXAMPLE_ID)
    client.cookies.set(name="access_token", value=access_token)
    client.cookies.set(name="refresh_token", value=refresh_token)

    return client


@pytest.fixture(name="fitness_trainer_client")
def fx_fitness_trainer_client_set_cookie(client: AsyncClient) -> AsyncClient:
    access_token = create_access_token(
        user_id=constants.FITNESS_TRAINER_ID,
        email=constants.FITNESS_TRAINER_EMAIL,
    )
    refresh_token = create_refresh_token(user_id=constants.FITNESS_TRAINER_ID)
    client.cookies.set(name="access_token", value=access_token)
    client.cookies.set(name="refresh_token", value=refresh_token)

    return client
