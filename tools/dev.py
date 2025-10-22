from __future__ import annotations

import typer
import uvicorn

from app.main import create_app

cli = typer.Typer(help="Developer utilities for the WhiteBalloon project.")


@cli.command()
def runserver(
    host: str = typer.Option("127.0.0.1", help="Interface to bind the development server"),
    port: int = typer.Option(8000, help="Port to bind the development server"),
    reload: bool = typer.Option(True, help="Enable auto-reload on code changes"),
) -> None:
    """Start the FastAPI application using uvicorn."""

    uvicorn.run(create_app(), host=host, port=port, reload=reload)


@cli.command()
def init_db() -> None:
    """Initialize the local database (implemented in Stage 2)."""

    typer.echo("Database initialization not yet implemented. Complete Stage 2 first.")


@cli.command()
def create_admin() -> None:
    """Create an administrator account (implemented in Stage 3)."""

    typer.echo("Admin creation not yet implemented. Complete Stage 3 first.")


if __name__ == "__main__":
    cli()
