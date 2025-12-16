from app.server.core import create_app

app = create_app()


def run_cli() -> None:
    """Entry point for the command-line interface (CLI).

    Initializes the main Typer application and integrates multiple command groups
    to provide comprehensive tooling for the application.

    The following command groups are included:

    * **Server Management:** Commands for running the application in development (`dev`)
      and production (`run`) mode.
    * **Database Migrations:** Commands for managing database schemas and migrations
      (provided by `advanced_alchemy`).
    * **Custom Tools:** Application-specific commands, such as those for user management.

    Examples:
        1. Start Development Server:
            ``app server dev``
        2. View Database Help:
            ``app database --help``
        3. Apply Migrations:
            ``app database upgrade head``
        4. View User Management Help:
            ``app users --help``
        5. Create New User:
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
