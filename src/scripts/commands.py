from __future__ import annotations

from typing import Any

import click
from rich import get_console

console = get_console()


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context  # type: ignore[arg-type]
def user_management_group(_: dict[str, Any]) -> None:
    """Manage application users."""


@user_management_group.command(name="create-user", help="Create a user")
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

    from config.app_settings import alchemy
    from domain.users.deps import provide_users_service
    from domain.users.schemas import UserCreate

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
                console.print(f"User created with email: {user.email}")
            except DuplicateKeyError:
                console.print(
                    f"User with email {obj_in.email!r} already exists in the database",
                    style="#FF0000",
                )

    console.rule("Create a new application user.")
    name = name or click.prompt("Full Name", show_default=False)
    email = email or click.prompt("Email")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create a superuser?", show_default=True, type=click.BOOL)
    anyio.run(_create_user, cast("str", email), cast("str", password), name, cast("bool", superuser))


@user_management_group.command("promote-to-superuser", help="Promotes a user to application superuser")
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

    from config.app_settings import alchemy
    from domain.users.schemas import UserUpdate
    from domain.users.services import UserService

    async def _promote_to_superuser(email: str) -> None:
        async with alchemy.with_async_session() as db_session:
            async with UserService.new(session=db_session) as users_service:
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
                    console.print(f"Upgraded user with email: {user.email} to superuser", style="#ffff00")
                else:
                    console.print(f"User with email: {email!r} not found", style="#FF0000")

    console.rule("Promote user to superuser.")
    email = email or click.prompt("Email")
    anyio.run(_promote_to_superuser, email)
