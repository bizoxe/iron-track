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
    from click import echo
    from click.exceptions import Abort, ClickException, Exit
    from typer import Typer
    from typer.main import get_group

    from app.scripts.commands import user_management_group
    from app.server.server_cli import server_cli_group

    main_cli = Typer(
        name="main_cli",
        help="Main CLI for IronTrack application.",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    main_cli.add_typer(server_cli_group)
    click_app = get_group(main_cli)
    click_app.add_command(register_database_commands(app), name="database")
    # typer >= 0.26 vendors its own copy of click: TyperGroup.add_command is typed
    # against the vendored Command, so a real click.Group fails the static check
    click_app.add_command(user_management_group, name="users")  # type: ignore[arg-type]
    # The vendored runner catches only vendored exceptions; ClickException/Exit/Abort
    # raised by real-click commands (e.g. `raise click.Abort` in commands.py)
    # would escape as raw tracebacks without this.
    try:
        click_app()
    except ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except Exit as e:
        sys.exit(e.exit_code)
    except Abort:
        echo("Aborted!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
