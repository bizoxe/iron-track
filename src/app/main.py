from app.server.core import create_app

app = create_app()


def run_cli() -> None:
    """Entry point for the command-line interface (CLI).

    Initializes the main application entry point (based on Typer)
    and integrates multiple command groups to provide comprehensive tooling:

    * Server Management: Commands for running the application in development
      (`dev`) and production (`run`) mode, using custom default settings for the entrypoint.
    * Database Migrations: Commands for managing database schemas and migrations
      provided by `advanced_alchemy`.
    * Custom Tools: Application-specific commands, such as those for user management.

    It collects these command groups and executes the CLI application.

    Example:
        1. Start Development Server:
           Start the server in development mode, automatically using the default app entrypoint.
           ``app server dev``

        2. View Database Help:
           View available Advanced Alchemy database commands (e.g., upgrade, revision, stamp).
           ``app database --help``

        3. Apply Migrations:
           Apply all pending database migrations.
           ``app database upgrade head``

        4. View User Management Help:
           View available user management subcommands.
           ``app users --help``

        5. Create New User:
           Create a new user account via the custom command group.
           ``app users create-user --name "User Example" --email user@example.com --password secretpwd``
    """
    from advanced_alchemy.extensions.fastapi.cli import register_database_commands
    from typer import Typer
    from typer.main import get_group

    from app.scripts.commands import user_management_group
    from app.utils.server_cli import server_cli_group

    main_cli = Typer(
        name="main_cli",
        help="Main CLI for IronTrack application.",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    main_cli.add_typer(server_cli_group)
    click_app = get_group(main_cli)
    click_app.add_command(register_database_commands(app), name="database")
    click_app.add_command(user_management_group, name="users")
    click_app()


if __name__ == "__main__":
    run_cli()
