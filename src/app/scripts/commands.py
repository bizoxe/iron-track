"""CLI commands for user management."""

# Deferred imports: keeps `--help` free of the config/database stack and
# lets each command pull only the dependencies it actually uses.

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click
from rich import get_console

if TYPE_CHECKING:
    from pydantic import ValidationError

    from app.db.models.role import Role as RoleModel
    from app.domain.accounts.services import RoleService

console = get_console()


@click.group(name="users", invoke_without_command=False, help="Manage application users and roles.")
@click.pass_context
def user_management_group(_: click.Context) -> None:
    """Manage application users and roles."""


async def require_roles(
    roles_service: RoleService,
    slugs: list[str],
) -> dict[str, RoleModel]:
    """Return roles by slug.

    Raises click.Abort if any requested role is not seeded.
    """
    roles = {slug: await roles_service.get_one_or_none(slug=slug) for slug in slugs}
    if missing := [slug for slug, role in roles.items() if role is None]:
        console.print(f"Application roles are not seeded: {', '.join(missing)}", style="red")
        console.print("Run 'app users create-roles' first", style="red")
        raise click.Abort

    return cast("dict[str, RoleModel]", roles)


def format_validation_errors(exc: ValidationError) -> str:
    """Format validation errors for CLI output."""
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        ctx = error.get("ctx", {})
        message = ctx.get("reason") or ctx.get("error") or error["msg"]
        messages.append(f"{field}: {message}")

    return "\n".join(messages)


@user_management_group.command(name="create-user", help="Create a user.")
@click.option(
    "--name",
    help="Full name of the new user",
)
@click.option(
    "--email",
    help="Email of the new user",
)
@click.option(
    "--password",
    help="User password",
)
@click.option(
    "--superuser/--no-superuser",
    help="Make the user a superuser",
    default=None,
)
def create_user(
    name: str | None,
    email: str | None,
    password: str | None,
    superuser: bool | None,
) -> None:
    """Create a new user."""
    import anyio
    from advanced_alchemy.exceptions import DuplicateKeyError
    from pydantic import ValidationError

    from app.config.app_settings import sqlalchemy_config
    from app.config.constants import DEFAULT_USER_ROLE_SLUG, SUPERUSER_ROLE_SLUG
    from app.domain.accounts.deps import provide_roles_service, provide_users_service
    from app.domain.accounts.schemas import UserCreate

    async def _create_user(
        name: str,
        email: str,
        password: str,
        superuser: bool,
    ) -> None:
        try:
            obj_in = UserCreate(
                name=name,
                email=email,
                password=password,
            )
            async with sqlalchemy_config.get_session() as db_session:
                users_service = await anext(provide_users_service(db_session))
                roles_service = await anext(provide_roles_service(db_session))
                roles = await require_roles(
                    roles_service=roles_service,
                    slugs=[DEFAULT_USER_ROLE_SLUG, SUPERUSER_ROLE_SLUG],
                )
                default_role, superuser_role = roles[DEFAULT_USER_ROLE_SLUG], roles[SUPERUSER_ROLE_SLUG]
                extra_fields: dict[str, Any] = {"role_id": default_role.id}
                if superuser:
                    extra_fields["role_id"] = superuser_role.id
                    extra_fields["is_superuser"] = True
                user_obj = await users_service.create(
                    data=obj_in.model_dump() | extra_fields,
                    auto_commit=True,
                )
                console.print(f"User created successfully with email '{user_obj.email}'", style="green")
        except (DuplicateKeyError, ValidationError) as exc:
            if isinstance(exc, DuplicateKeyError):
                console.print(f"User already exists: {email}", style="red")
            else:
                console.print(format_validation_errors(exc), style="red")

    console.rule("Create a new application user.")
    name = name or click.prompt("Full Name")
    email = email or click.prompt("Email")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    if superuser is None:
        superuser = click.confirm("Promote to superuser", default=False)
    anyio.run(_create_user, name, email, password, superuser)


@user_management_group.command(name="promote-to-superuser", help="Promote a user to application superuser.")
@click.option(
    "--email",
    help="Email of the user",
)
def promote_to_superuser(email: str | None) -> None:
    """Promote a user to superuser."""
    import anyio

    from app.config.app_settings import sqlalchemy_config
    from app.config.constants import SUPERUSER_ROLE_SLUG
    from app.domain.accounts.deps import provide_roles_service, provide_users_service

    async def _promote_to_superuser(email: str) -> None:
        async with sqlalchemy_config.get_session() as db_session:
            users_service = await anext(provide_users_service(db_session))
            roles_service = await anext(provide_roles_service(db_session))
            roles = await require_roles(roles_service=roles_service, slugs=[SUPERUSER_ROLE_SLUG])
            superuser_role = roles[SUPERUSER_ROLE_SLUG]
            user_obj = await users_service.get_one_or_none(email=email)
            if user_obj is not None:
                console.print(f"Promoting user: {user_obj.email}", style="green")
                to_update = {"is_superuser": True, "role_id": superuser_role.id}
                updated_user = await users_service.update(
                    item_id=user_obj.id,
                    data=to_update,
                    auto_commit=True,
                )
                console.print(f"Promoted user with email '{updated_user.email}' to superuser", style="green")
            else:
                console.print(f"User not found: {email}", style="red")

    console.rule("Promote user to superuser.")
    email = email or click.prompt("Email")
    anyio.run(_promote_to_superuser, email)


@user_management_group.command(name="create-system-admin", help="Create system default administrator.")
@click.option(
    "--password",
    envvar="ADMIN_PASSWORD",
    show_envvar=True,
    help="Admin password",
)
def create_system_admin(password: str | None) -> None:
    """Create system default administrator."""
    import anyio
    from advanced_alchemy.exceptions import DuplicateKeyError
    from pydantic import ValidationError

    from app.config.app_settings import sqlalchemy_config
    from app.config.constants import DEFAULT_ADMIN_EMAIL, SUPERUSER_ROLE_SLUG
    from app.domain.accounts.deps import provide_roles_service, provide_users_service
    from app.domain.accounts.schemas import UserCreate

    async def _create_system_admin(password: str) -> None:
        try:
            obj_in = UserCreate(
                name="System Administrator",
                email=DEFAULT_ADMIN_EMAIL,
                password=password,
            )
            async with sqlalchemy_config.get_session() as db_session:
                users_service = await anext(provide_users_service(db_session))
                roles_service = await anext(provide_roles_service(db_session))
                roles = await require_roles(roles_service=roles_service, slugs=[SUPERUSER_ROLE_SLUG])
                superuser_role = roles[SUPERUSER_ROLE_SLUG]
                await users_service.create(
                    data=obj_in.model_dump() | {"is_superuser": True, "role_id": superuser_role.id},
                    auto_commit=True,
                )
                console.print("System administrator created successfully", style="green")
        except DuplicateKeyError:
            console.print("System administrator already exists — skipping", style="yellow")
        except ValidationError as exc:
            console.print(format_validation_errors(exc), style="red")
            raise click.Abort from None

    console.rule("Create system administrator.")
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    anyio.run(_create_system_admin, password)


@user_management_group.command(name="create-roles", help="Create or update pre-configured application roles.")
def create_default_roles() -> None:
    """Synchronize default application roles."""
    from pathlib import Path

    import anyio
    from advanced_alchemy.utils.fixtures import open_fixture_async

    from app.config.app_settings import sqlalchemy_config
    from app.config.base import get_settings
    from app.domain.accounts.deps import provide_roles_service

    async def _create_default_roles() -> None:
        settings = get_settings()
        fixture_path = Path(settings.db.FIXTURE_PATH)
        async with sqlalchemy_config.get_session() as db_session:
            roles_service = await anext(provide_roles_service(db_session))
            fixture = await open_fixture_async(fixture_path, "role")
            await roles_service.upsert_many(match_fields=["name"], data=fixture, auto_commit=True)
            console.print("Successfully loaded and synchronized default roles", style="green")

    console.rule("Create default roles.")
    anyio.run(_create_default_roles)
