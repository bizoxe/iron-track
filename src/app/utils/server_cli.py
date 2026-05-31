"""Server management module.

This module provides the `server_cli_group`, a Typer-based interface for launching
the application using different server engines.

It offers two main modes:
- `dev`: A development-oriented mode (Uvicorn) with auto-reload.
- `run`: A production-like performance testing mode (Granian).
"""

from typing import (
    Annotated,
    Any,
    Final,
    TypedDict,
)

import typer
import uvicorn
from granian import Granian
from granian.constants import (
    Interfaces,
    Loops,
    RuntimeModes,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Option, Typer

from app.config.base import get_settings

settings = get_settings()

TARGET_APP_FACTORY: Final[str] = "src.app.server.core:create_app"


server_cli_group = Typer(
    name="server",
    help=(
        "Commands for running the application [bold yellow]server[/bold yellow] ([green]dev[/green], [blue]run[/blue])."
    ),
    no_args_is_help=True,
)


class UvicornParams(TypedDict):
    """Configuration schema for Uvicorn server."""

    app: str
    host: str
    port: int
    reload: bool
    reload_dirs: list[str] | None
    proxy_headers: bool
    forwarded_allow_ips: str | None
    log_config: Any | None
    workers: int | None
    factory: bool


class GranianParams(TypedDict):
    """Configuration schema for Granian server."""

    target: str
    address: str
    port: int
    interface: Interfaces
    workers: int
    runtime_threads: int
    runtime_mode: RuntimeModes
    loop: Loops
    backlog: int
    log_dictconfig: dict[str, Any] | None
    log_enabled: bool
    log_access: bool
    factory: bool


def start_server(
    uv_params: UvicornParams | None = None,
    gr_params: GranianParams | None = None,
) -> None:
    """Start the specified server (Granian or Uvicorn)."""
    if uv_params:
        uvicorn.run(**uv_params)

    if gr_params:
        server = Granian(**gr_params)
        server.serve()


def uvicorn_table_rows(table: Table, params: UvicornParams) -> None:
    """Append Uvicorn configuration rows to the status table."""
    host = params["host"]
    port = params["port"]
    base_url = f"http://{host}:{port}"

    table.add_row("Server:", "Uvicorn")
    table.add_row("Reload:", "Enabled")
    table.add_row("Address:", f"[link={base_url}]{base_url}[/link]")
    table.add_row("Swagger:", f"[link={base_url}/docs]{base_url}/docs[/link]")


def granian_table_rows(table: Table, params: GranianParams) -> None:
    """Append Granian configuration rows to the status table."""
    host = params["address"]
    port = params["port"]
    base_url = f"http://{host}:{port}"

    table.add_row("Server:", "Granian")
    table.add_row("Address:", f"[link={base_url}]{base_url}[/link]")
    table.add_row("Workers:", str(params["workers"]))
    table.add_row("Runtime Threads:", str(params["runtime_threads"]))
    table.add_row("Runtime Mode:", str(params["runtime_mode"]))
    table.add_row("Loop:", str(params["loop"]))
    table.add_row("Backlog:", str(params["backlog"]))


def print_startup_info(
    uv_params: UvicornParams | None = None,
    gr_params: GranianParams | None = None,
) -> None:
    """Display startup configuration in a formatted table."""
    console = Console()

    table = Table(show_header=False, box=None)
    table.add_column(style="cyan")
    table.add_column(style="magenta")
    if uv_params:
        uvicorn_table_rows(table=table, params=uv_params)
    if gr_params:
        granian_table_rows(table=table, params=gr_params)

    console.print(Panel(table, title="[bold blue]IronTrack Startup[/bold blue]"))
    console.print("[bold green]Starting server... [/bold green]")


@server_cli_group.command("dev")
def dev(  # noqa: PLR0913
    *,
    host: Annotated[
        str,
        typer.Option(
            help=(
                "The host to serve on. For local development in localhost use [blue]127.0.0.1[/blue]. To "
                "enable public access, e.g. in a container, use all the IP addresses available with "
                "[blue]0.0.0.0[/blue]."
            )
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        Option(
            help=(
                "The port to serve on. You would normally have a termination proxy on top (another program) "
                "handling HTTPS on port [blue]443[/blue] and HTTP on port [blue]80[/blue], transferring the "
                "communication to your app."
            ),
            envvar="PORT",
        ),
    ] = 8000,
    reload: Annotated[
        bool,
        Option(
            help=(
                "Enable auto-reload of the server when (code) files change. This is [bold]resource "
                "intensive[/bold], use it only during development."
            )
        ),
    ] = True,
    reload_dir: Annotated[
        list[str] | None,
        Option(help="Set reload directories explicitly, instead of using the current working directory."),
    ] = None,
    proxy_headers: Annotated[
        bool,
        Option(
            help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port to populate remote address info."
        ),
    ] = True,
    forwarded_allow_ips: Annotated[
        str | None,
        Option(
            help=(
                "Comma separated list of IP Addresses to trust with proxy headers. The literal '*' means trust "
                "everything."
            )
        ),
    ] = None,
) -> Any:
    """Run the server in [green]development-like mode[/green] (using Uvicorn) with auto-reload."""
    params: UvicornParams = {
        "app": TARGET_APP_FACTORY,
        "host": host,
        "port": port,
        "reload": reload,
        "reload_dirs": reload_dir,
        "proxy_headers": proxy_headers,
        "forwarded_allow_ips": forwarded_allow_ips,
        "log_config": None,
        "workers": None,
        "factory": True,
    }
    print_startup_info(
        uv_params=params,
    )
    start_server(uv_params=params)


@server_cli_group.command("run")
def run(  # noqa: PLR0913
    *,
    address: Annotated[
        str,
        Option(
            help=(
                "The address to bind to. Use [blue]127.0.0.1[/blue] for local access, "
                "or [blue]0.0.0.0[/blue] to bind to all available interfaces."
            )
        ),
    ] = "0.0.0.0",  # noqa: S104
    port: Annotated[
        int,
        Option(
            help=(
                "The port to serve on. You would normally have a termination proxy on top (another program) "
                "handling HTTPS on port [blue]443[/blue] and HTTP on port [blue]80[/blue], transferring the "
                "communication to your app."
            ),
            envvar="PORT",
        ),
    ] = 8000,
    workers: Annotated[
        int,
        Option(help="Number of worker processes. Increase for higher concurrency."),
    ] = 1,
    runtime_threads: Annotated[
        int,
        Option("--runtime-threads", help="Number of runtime threads per worker. Increase for high-load CPU tasks."),
    ] = 1,
    runtime_mode: Annotated[
        RuntimeModes,
        Option(
            "--runtime-mode",
            help=(
                "Runtime mode: [blue]mt[/blue] (multi-threaded), [blue]st[/blue] (single-threaded),"
                " or [blue]auto[/blue]."
            ),
        ),
    ] = RuntimeModes.auto,
    loop: Annotated[
        Loops,
        Option(help="Event loop implementation."),
    ] = Loops.auto,
    backlog: Annotated[
        int,
        Option(min=128, help="Maximum number of connections in backlog."),
    ] = 1024,
) -> Any:
    """Run the server in [green]production-like mode[/green] (using Granian) for performance testing."""
    params: GranianParams = {
        "target": TARGET_APP_FACTORY,
        "address": address,
        "port": port,
        "interface": Interfaces.ASGI,
        "workers": workers,
        "runtime_threads": runtime_threads,
        "runtime_mode": runtime_mode,
        "loop": loop,
        "backlog": backlog,
        "log_dictconfig": None,
        "log_enabled": True,
        "log_access": True,
        "factory": True,
    }
    print_startup_info(
        gr_params=params,
    )
    start_server(gr_params=params)
