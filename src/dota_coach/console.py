"""Centralized colored console output for the coach.

Keeps rich usage in one place so the rest of the code just calls these
helpers. Colors: events yellow, coach advice green, errors red.
"""

from rich.console import Console

_console = Console()


def event(text: str) -> None:
    """Print a detected event line."""
    _console.print(f"[yellow]• {text}[/yellow]")


def advice(label: str, text: str) -> None:
    """Print a coach advice line."""
    _console.print(f"[bold green]COACH[/bold green] [green]({label}): {text}[/green]")


def error(text: str) -> None:
    """Print an error line."""
    _console.print(f"[red]! {text}[/red]")


def info(text: str) -> None:
    """Print a discreet informational line (startup, heartbeat)."""
    _console.print(f"[dim]{text}[/dim]")