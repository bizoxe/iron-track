from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

import click
from rich import get_console

if TYPE_CHECKING:
    from src.db.models.role import Role as RoleModel

console = get_console()


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context
def user_management_group(_: dict[str, Any]) -> None:
    """Manage application users."""


def check_roles_created(roles: list[RoleModel | None]) -> list[RoleModel]:
    if not any(roles):
        console.print(
            "\n USER ROLES NOT CREATED",
            style="#FF0000",
        )
        console.print(
            "Kindly execute the create-roles command to initialize the database",
            style="#FF0000",
        )
        raise click.Abort()
    return cast("list[RoleModel]", roles)


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
    import anyio
    import click
    from advanced_alchemy.exceptions import DuplicateKeyError

    from src.config.app_settings import alchemy
    from src.config.constants import SUPERUSER_ROLE_SLUG
    from src.domain.users.deps import provide_role_service, provide_users_service

    async def _create_user(
        email: str,
        password: str,
        name: str | None = None,
        superuser: bool = False,
    ) -> None:
        obj_data = {
            "name": name,
            "email": email,
            "password": password,
            "is_superuser": superuser,
        }
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session=db_session))
            roles_service = await anext(provide_role_service(db_session=db_session))
            default_role = await roles_service.get_one_or_none(slug=users_service.default_role)
            superuser_role = await roles_service.get_one_or_none(slug=SUPERUSER_ROLE_SLUG)
            default_role, superuser_role = check_roles_created([default_role, superuser_role])
            try:
                user = await users_service.create(
                    data=obj_data | {"role_id": superuser_role.id if superuser else default_role.id},
                    auto_commit=True,
                )
                console.print(f"User created with email: {user.email}", style="#ffff00")
            except DuplicateKeyError:
                console.print(
                    f"User with email '{email}' already exists in the database",
                    style="#FF0000",
                )

    console.rule("Create a new application user.")
    name = name or click.prompt("Full Name", show_default=False)
    email = email or click.prompt("Email")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create a superuser (bool value)?", show_default=True, type=click.BOOL)
    anyio.run(_create_user, email, password, name, superuser)


@user_management_group.command(name="promote-to-superuser", help="Promotes a user to application superuser.")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=True,
    show_default=False,
)
def promote_to_superuser(email: str) -> None:
    """Promote to Superuser.

    Args:
        email (str): The email address of the user to promote.
    """
    import anyio

    from src.config.app_settings import alchemy
    from src.config.constants import SUPERUSER_ROLE_SLUG
    from src.domain.users.deps import provide_role_service, provide_users_service

    async def _promote_to_superuser(email: str) -> None:
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session=db_session))
            role_service = await anext(provide_role_service(db_session=db_session))
            superuser_role = await role_service.get_one_or_none(slug=SUPERUSER_ROLE_SLUG)
            superuser_role = check_roles_created([superuser_role])[0]
            user = await users_service.get_one_or_none(email=email)
            if user:
                console.print(f"Promoting user: {user.email}", style="#ffff00")
                obj_data = {"is_superuser": True, "role_id": superuser_role.id}
                user = await users_service.update(
                    item_id=user.id,
                    data=obj_data,
                    auto_commit=True,
                )
                console.print(f"Upgraded user with email: '{user.email}' to superuser", style="#ffff00")
            else:
                console.print(f"User with email: {email} not found", style="#FF0000")

    console.rule("Promote user to superuser.")
    anyio.run(_promote_to_superuser, email)


@user_management_group.command(name="create-system-admin", help="Create system default administrator.")
@click.option(
    "--password",
    help="Admin password",
    type=click.STRING,
    required=False,
    show_default=False,
)
def create_system_admin(password: str | None) -> None:
    """Create system default administrator."""
    import anyio
    import click

    from src.config.app_settings import alchemy
    from src.config.constants import DEFAULT_ADMIN_EMAIL, SUPERUSER_ROLE_SLUG
    from src.domain.users.deps import provide_role_service, provide_users_service

    async def _create_system_admin(password: str) -> None:
        obj_data = {
            "name": "System Administrator",
            "email": DEFAULT_ADMIN_EMAIL,
            "password": password,
            "is_superuser": True,
        }
        async with alchemy.with_async_session() as db_session:
            users_service = await anext(provide_users_service(db_session=db_session))
            role_service = await anext(provide_role_service(db_session=db_session))
            superuser_role = await role_service.get_one_or_none(slug=SUPERUSER_ROLE_SLUG)
            superuser_role = check_roles_created(roles=[superuser_role])[0]
            if not await users_service.exists(email=obj_data["email"]):
                await users_service.create(data=obj_data | {"role_id": superuser_role.id}, auto_commit=True)
                console.print("System administrator was created", style="#ffff00")
            else:
                console.print("System administrator already exists", style="#FF0000")

    console.rule("Create system administrator.")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    anyio.run(_create_system_admin, password)


@user_management_group.command(name="create-roles", help="Create pre-configured application roles.")
def create_default_roles() -> None:
    """Create the default Roles for the system."""
    from pathlib import Path

    import anyio
    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import select
    from sqlalchemy.orm import load_only

    from src.config.app_settings import alchemy
    from src.config.base import get_settings
    from src.db.models.role import Role
    from src.domain.users.services import RoleService

    async def _create_default_roles() -> None:
        settings = get_settings()
        fixture_path = Path(settings.db.FIXTURE_PATH)
        async with alchemy.with_async_session() as db_session:
            async with RoleService.new(
                statement=select(Role).options(load_only(Role.id, Role.slug, Role.name, Role.description)),
                session=db_session,
            ) as service:
                fixture_data = await open_fixture_async(fixture_path, "role")
                await service.upsert_many(match_fields=["name"], data=fixture_data, auto_commit=True)
                console.print("Successfully loaded and synchronized default roles", style="#ffff00")

    console.rule("Creating default roles.")
    anyio.run(_create_default_roles)
