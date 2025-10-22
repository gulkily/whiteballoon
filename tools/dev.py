from __future__ import annotations

import typer
import uvicorn

from app.db import init_db

cli = typer.Typer(help="Developer utilities for the WhiteBalloon project.")


@cli.command()
def runserver(
    host: str = typer.Option("127.0.0.1", help="Interface to bind the development server"),
    port: int = typer.Option(8000, help="Port to bind the development server"),
    reload: bool = typer.Option(True, help="Enable auto-reload on code changes"),
) -> None:
    """Start the FastAPI application using uvicorn."""

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, factory=False)


@cli.command(name="init-db")
def init_db_command() -> None:
    """Initialize the local database."""

    init_db()
    typer.echo("Database ready.")


@cli.command()
def create_admin() -> None:
    """Create an administrator account (implemented in Stage 3)."""

    typer.echo("Admin creation not yet implemented. Complete Stage 3 first.")


if __name__ == "__main__":
    cli()
