from __future__ import annotations

from typing import Any

import click
from rich import get_console

console = get_console()


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context
def user_management_group(_: dict[str, Any]) -> None:
    """Manage application users."""


async def load_database_fixtures() -> None:
    """Import/Synchronize Database Fixtures."""
    from pathlib import Path

    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import select
    from sqlalchemy.orm import load_only
    from structlog import get_logger

    from src.config.app_settings import alchemy
    from src.config.base import get_settings
    from src.db.models.role import Role
    from src.domain.users.services import RoleService

    logger = get_logger()
    settings = get_settings()
    fixture_path = Path(settings.db.FIXTURE_PATH) # type: ignore[attr-defined]
    async with alchemy.with_async_session() as db_session:
        async with RoleService.new(
            statement=select(Role).options(load_only(Role.id, Role.slug, Role.name, Role.description)),
            session=db_session,
        ) as service:
            fixture_data = await open_fixture_async(fixture_path, "role")
            await service.upsert_many(match_fields=["name"], data=fixture_data, auto_commit=True)
            await logger.ainfo("loaded roles")


@user_management_group.command(name="create-user", help="Create a user.")
@click.option(
    "--name",
    help="A name of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--email",
    help="Email of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--password",
    help="User password",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--superuser",
    help="Is a superuser",
    type=click.BOOL,
    required=False,
    show_default=False,
    default=False,
    is_flag=True,
)
def create_user(
    name: str | None,
    email: str | None,
    password: str | None,
    superuser: bool | None,
) -> None:
    """Create a new user."""
    from typing import cast

    import anyio
    import click
    from advanced_alchemy.exceptions import DuplicateKeyError

    from src.config.app_settings import alchemy
    from src.domain.users.deps import provide_users_service
    from src.domain.users.schemas import UserCreate

    async def _create_user(
        email: str,
        password: str,
        name: str | None = None,
        superuser: bool = False,
    ) -> None:
        obj_in = UserCreate(
            name=name,
            email=email,
            password=password,
            is_superuser=superuser,
        )
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session))
            try:
                user = await users_service.create(data=obj_in, auto_commit=True)
                console.print(f"User created with email: {user.email}", style="#ffff00")
            except DuplicateKeyError:
                console.print(
                    f"User with email '{obj_in.email}' already exists in the database",
                    style="#FF0000",
                )

    console.rule("Create a new application user.")
    name = name or click.prompt("Full Name", show_default=False)
    email = email or click.prompt("Email")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create a superuser (bool value)?", show_default=True, type=click.BOOL)
    anyio.run(_create_user, cast("str", email), cast("str", password), name, cast("bool", superuser))


@user_management_group.command(name="promote-to-superuser", help="Promotes a user to application superuser.")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: str) -> None:
    """Promote to Superuser.

    Args:
        email (str): The email address of the user to promote.
    """
    import anyio
    import click

    from src.config.app_settings import alchemy
    from src.domain.users.deps import provide_users_service
    from src.domain.users.schemas import UserUpdate

    async def _promote_to_superuser(email: str) -> None:
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session=db_session))
            user = await users_service.get_one_or_none(email=email)
            if user:
                console.print(f"Promoting user: {user.email}", style="#ffff00")
                user_to_update = UserUpdate(
                    email=email,
                    is_superuser=True,
                )
                user = await users_service.update(
                    item_id=user.id,
                    data=user_to_update,
                    auto_commit=True,
                )
                console.print(f"Upgraded user with email: '{user.email}' to superuser", style="#ffff00")
            else:
                console.print(f"User with email: {email} not found", style="#FF0000")

    console.rule("Promote user to superuser.")
    email = email or click.prompt("Email")
    anyio.run(_promote_to_superuser, email)


@user_management_group.command(name="create-roles", help="Create pre-configured application roles and assign to users.")
def create_default_roles() -> None:
    """Create the default Roles for the system."""
    from typing import TYPE_CHECKING

    import anyio
    from advanced_alchemy.utils.text import slugify

    from src.config.app_settings import alchemy
    from src.config.constants import SUPERUSER_ACCESS_ROLE
    from src.db.models.user_role import UserRole
    from src.domain.users.deps import provide_role_service, provide_users_service

    if TYPE_CHECKING:
        from collections.abc import Sequence

        from src.db.models.role import Role
        from src.db.models.user import User

    def _assign_role_to_users(users: Sequence[User], role: Role, role_name: str) -> None:
        for user in users:
            if any(r.role_id == role.id for r in user.roles):
                console.print(f"User '{user.email}' already has a {role_name} role", style="#FF0000")
            else:
                user.roles.append(UserRole(role_id=role.id))
                console.print(f"Assigned '{user.email}' {role_name} role", style="#ffff00")

    async def _create_default_roles() -> None:
        await load_database_fixtures()
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session=db_session))
            roles_service = await anext(provide_role_service(db_session=db_session))
            superuser_role = await roles_service.get_one_or_none(slug=slugify(SUPERUSER_ACCESS_ROLE))
            default_user_role = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
            if default_user_role:
                all_active_users = await users_service.list(is_active=True, is_superuser=False)
                _assign_role_to_users(
                    users=all_active_users,
                    role=default_user_role,
                    role_name="default",
                )
            if superuser_role:
                all_superusers = await users_service.list(is_superuser=True)
                _assign_role_to_users(
                    users=all_superusers,
                    role=superuser_role,
                    role_name="superuser",
                )
            await db_session.commit()

    console.rule("Creating default roles.")
    anyio.run(_create_default_roles)
