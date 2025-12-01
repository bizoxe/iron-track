from src.server.core import create_app

app = create_app()


if __name__ == "__main__":
    """Launches the FastAPI CLI with the database commands registered
    Run `uv run examples/fastapi/fastapi_service.py --help` to launch the FastAPI CLI with the database commands
    registered
    """
    from advanced_alchemy.extensions.fastapi.cli import register_database_commands
    from fastapi_cli.cli import app as fastapi_cli_app
    from typer.main import get_group

    click_app = get_group(fastapi_cli_app)
    click_app.add_command(register_database_commands(app))
    click_app()
