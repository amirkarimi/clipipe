#!/usr/bin/env python3

import sys

import click
import requests
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True)

DEFAULT_SERVER_URL = "https://clipipe.io"


def _log_error(message: str):
    """Log an error message to the error console."""
    error_console.print(f"[red]Error:[/red] {message}")


@click.group()
@click.option(
    "--server",
    default=DEFAULT_SERVER_URL,
    envvar="CLIPIPE_SERVER",
    help=f"Server URL (default: {DEFAULT_SERVER_URL} or set CLIPIPE_SERVER environment variable)",
)
@click.pass_context
def cli(ctx, server):
    """Clipipe - Send and receive data using human-readable codes."""
    ctx.ensure_object(dict)
    ctx.obj["server"] = server


@cli.command()
@click.pass_context
def send(ctx):
    """Send data from stdin to the server and get a retrieval code.

    Examples:
        echo "Hello World" | clipipe send
        cat file.txt | clipipe send
        clipipe send < data.json
    """
    server_url = ctx.obj["server"]

    if sys.stdin.isatty():
        error_console.print(
            "[red]Error:[/red] No input detected. Please pipe data to this command.",
        )
        error_console.print(
            "\n[yellow]Examples:[/yellow]\n"
            "  echo 'Hello World' | clipipe send\n"
            "  cat file.txt | clipipe send\n"
            "  clipipe send < data.json",
        )
        sys.exit(1)

    try:
        data = sys.stdin.buffer.read()
        if not data:
            _log_error("No data received from stdin")
            sys.exit(1)

        with console.status("[bold blue]Sending data to server..."):
            response = requests.post(
                f"{server_url}/store",
                data=data,
                timeout=10,
                headers={"Content-Type": "application/octet-stream"},
            )
            response.raise_for_status()

        result = response.json()
        code = result["code"]
        expires_in = result["expires_in"]

        console.print(f"[dim]To retrieve: [/dim][bold]clipipe receive [green]{code}[/green][/bold]")
        console.print(f"[dim]Expires in: [/dim][bold]{expires_in} seconds[/bold]")

    except requests.exceptions.RequestException as e:
        _log_error(f"Filed to connect to server: {e}")
        sys.exit(1)
    except Exception as e:
        _log_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument("code")
@click.pass_context
def receive(ctx, code):
    """Retrieve data using a code.

    Examples:
        clipipe receive abc123
        clipipe receive abc123 > output.txt
    """
    server_url = ctx.obj["server"]

    try:
        with console.status("[bold blue]Retrieving data from server..."):
            response = requests.get(f"{server_url}/retrieve/{code}", timeout=10)

        if response.status_code == 404:
            _log_error("Code not found or expired")
            sys.exit(1)

        response.raise_for_status()
        data = response.content
        sys.stdout.buffer.write(data)
    except requests.exceptions.RequestException as e:
        _log_error(f"Failed to connect to server: {e}")
        sys.exit(1)
    except Exception as e:
        _log_error(str(e))
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Check server status."""
    server_url = ctx.obj["server"]

    try:
        with console.status("[bold blue]Checking server status..."):
            response = requests.get(f"{server_url}/health", timeout=5)
            response.raise_for_status()

        health_data = response.json()

        table = Table(title="Server Status", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        table.add_row("Server", "✅ online")
        redis_status = health_data.get('redis', 'unknown')
        icon = "✅" if redis_status == "connected" else "❌"
        table.add_row("Redis", f"{icon} {redis_status}")
        table.add_row("URL", server_url)

        console.print(table)

    except requests.exceptions.RequestException as e:
        _log_error(f"Server unreachable: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()

