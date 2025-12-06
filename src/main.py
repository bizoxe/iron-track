from src.server.core import create_app

app = create_app()


def run_cli() -> None:
    """Entry point for the command-line interface (CLI).

    This function configures and runs the command-line interface by integrating
    multiple command groups:

    * The base commands from `fastapi_cli`.
    * Database migration commands from `advanced_alchemy`.
    * Custom application-specific commands for user management.

    It retrieves the Typer application group, registers the necessary
    command groups, and then executes the CLI.

    Example:
        1. **Start Development Server:**
           Start the server in development mode, explicitly specifying the app entrypoint.

           ``python -m src.main dev -e src.main:app``

        2. **View Database Help:**
           View available Advanced Alchemy database commands (e.g., upgrade, revision, stamp).

           ``python -m src.main database --help``

        3. **Apply Migrations:**
           Apply all pending database migrations.

           ``python -m src.main database upgrade head``

        4. **View User Management Help:**
           View available user management subcommands.

           ``python -m src.main users --help``

        5. **Create New User:**
           Create a new user account via the custom command group.

           ``python -m src.main users create-user --name "User Example" --email user@example.com --password secretpwd``
    """
    from advanced_alchemy.extensions.fastapi.cli import register_database_commands
    from fastapi_cli.cli import app as fastapi_cli_app
    from typer.main import get_group

    from src.scripts.commands import user_management_group

    click_app = get_group(fastapi_cli_app)
    click_app.add_command(register_database_commands(app))
    click_app.add_command(user_management_group)
    click_app()


if __name__ == "__main__":
    run_cli()
