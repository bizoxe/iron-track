"""A module for CLI to manage the server.

This module defines a custom Typer group (`server_cli_group`) that wraps the base
`fastapi dev` and `fastapi run` commands from `fastapi-cli`.

The main purpose of this wrapper is to provide a consistent and explicit
`DEFAULT_ENTRYPOINT` for the application, minimizing boilerplate configuration
for the developer.

This group is intended to be mounted onto the main application CLI.
"""

from pathlib import Path
from typing import (
    Annotated,
    Any,
    Final,
)

import typer
from fastapi_cli.cli import dev as fastapi_cli_dev
from fastapi_cli.cli import run as fastapi_cli_run
from typer import Typer

DEFAULT_ENTRYPOINT: Final[str] = "app.main:app"


server_cli_group = Typer(
    name="server",
    help=(
        "🚀 Commands for running the application [bold yellow]server[/bold yellow]"
        " ([green]dev[/green], [blue]run[/blue])."
    ),
    no_args_is_help=True,
)


@server_cli_group.command("dev")
def dev(  # noqa: PLR0913
    path: Annotated[
        Path | None,
        typer.Argument(
            help=(
                "A path to a Python file or package directory (with [blue]__init__.py[/blue] files) "
                "containing a [bold]FastAPI[/bold] app. If not provided, a default set of paths will be tried."
            )
        ),
    ] = None,
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
        typer.Option(
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
        typer.Option(
            help=(
                "Enable auto-reload of the server when (code) files change. This is [bold]resource "
                "intensive[/bold], use it only during development."
            )
        ),
    ] = True,
    root_path: Annotated[
        str,
        typer.Option(
            help=(
                "The root path is used to tell your app that it is being served to the outside world with "
                "some [bold]path prefix[/bold] set up in some termination proxy or similar."
            )
        ),
    ] = "",
    app: Annotated[
        str | None,
        typer.Option(
            help=(
                "The name of the variable that contains the [bold]FastAPI[/bold] app in the imported module or "
                "package. If not provided, it is detected automatically."
            )
        ),
    ] = None,
    entrypoint: Annotated[
        str | None,
        typer.Option(
            "--entrypoint",
            "-e",
            help="The FastAPI app import string in the format 'some.importable_module:app_name'.",
        ),
    ] = DEFAULT_ENTRYPOINT,
    proxy_headers: Annotated[
        bool,
        typer.Option(
            help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port to populate remote address info."
        ),
    ] = True,
    forwarded_allow_ips: Annotated[
        str | None,
        typer.Option(
            help=(
                "Comma separated list of IP Addresses to trust with proxy headers. The literal '*' means trust "
                "everything."
            )
        ),
    ] = None,
) -> Any:
    """Run a FastAPI app in [green]development mode[/green]."""
    fastapi_cli_dev(
        path=path,
        host=host,
        port=port,
        reload=reload,
        root_path=root_path,
        app=app,
        entrypoint=entrypoint,
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
    )


@server_cli_group.command("run")
def run(  # noqa: PLR0913
    path: Annotated[
        Path | None,
        typer.Argument(
            help=(
                "A path to a Python file or package directory (with [blue]__init__.py[/blue] files) containing"
                " a [bold]FastAPI[/bold] app. If not provided, a default set of paths will be tried."
            )
        ),
    ] = None,
    *,
    host: Annotated[
        str,
        typer.Option(
            help=(
                "The host to serve on. For local development in localhost use [blue]127.0.0.1[/blue]. To enable"
                " public access, e.g. in a container, use all the IP addresses available with [blue]0.0.0.0[/blue]."
            )
        ),
    ] = "0.0.0.0",  # noqa: S104
    port: Annotated[
        int,
        typer.Option(
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
        typer.Option(
            help=(
                "Enable auto-reload of the server when (code) files change. This is [bold]resource "
                "intensive[/bold], use it only during development."
            )
        ),
    ] = False,
    workers: Annotated[
        int | None,
        typer.Option(help="Use multiple worker processes. Mutually exclusive with the --reload flag."),
    ] = None,
    root_path: Annotated[
        str,
        typer.Option(
            help=(
                "The root path is used to tell your app that it is being served to the outside world with "
                "some [bold]path prefix[/bold] set up in some termination proxy or similar."
            )
        ),
    ] = "",
    app: Annotated[
        str | None,
        typer.Option(
            help=(
                "The name of the variable that contains the [bold]FastAPI[/bold] app in the imported module "
                "or package. If not provided, it is detected automatically."
            )
        ),
    ] = None,
    entrypoint: Annotated[
        str | None,
        typer.Option(
            "--entrypoint",
            "-e",
            help="The FastAPI app import string in the format 'some.importable_module:app_name'.",
        ),
    ] = DEFAULT_ENTRYPOINT,
    proxy_headers: Annotated[
        bool,
        typer.Option(
            help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port to populate remote address info."
        ),
    ] = True,
    forwarded_allow_ips: Annotated[
        str | None,
        typer.Option(
            help=(
                "Comma separated list of IP Addresses to trust with proxy headers. The literal '*' means trust "
                "everything."
            )
        ),
    ] = None,
) -> Any:
    """Run a FastAPI app in [green]production mode[/green]."""
    fastapi_cli_run(
        path=path,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        root_path=root_path,
        app=app,
        entrypoint=entrypoint,
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
    )
