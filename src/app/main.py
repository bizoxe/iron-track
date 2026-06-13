from app.server.core import create_app

app = create_app()


def run_cli() -> None:
    """Entry point for the command-line interface (CLI).

    Initializes the main Typer application and integrates multiple command groups
    to provide comprehensive tooling for the application.

    Example:
        .. code-block:: bash

            # Server management
            app server dev
            app server run

            # Database management
            app database --help
            app database upgrade head

            # User management
            app users --help
            app users create-user --name "John Doe" --email john@example.com --password secret
    """
    import sys

    from advanced_alchemy.extensions.fastapi.cli import register_database_commands
    from click.exceptions import Exit
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
    click_app.add_command(user_management_group, name="users")  # type: ignore[arg-type]
    try:
        click_app()
    except Exit as e:
        sys.exit(e.exit_code)


if __name__ == "__main__":
    run_cli()
