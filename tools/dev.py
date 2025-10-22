from __future__ import annotations

from typing import Optional

import typer
import uvicorn
from sqlmodel import Session, select

from app.db import get_engine, init_db
from app.models import User
from app.services import auth_service

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


@cli.command(name="create-admin")
def create_admin(username: str) -> None:
    """Promote an existing user to administrator."""

    engine = get_engine()
    normalized = auth_service.normalize_username(username)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == normalized)).first()
        if not user:
            typer.echo(f"User '{normalized}' not found. Register the user first.")
            raise typer.Exit(code=1)
        user.is_admin = True
        session.commit()
        typer.echo(f"User '{normalized}' promoted to admin.")


@cli.command(name="create-invite")
def create_invite(
    username: Optional[str] = typer.Option(None, help="Existing admin username to attribute the invite to"),
    max_uses: int = typer.Option(1, min=1, help="Maximum number of times the invite can be used"),
    expires_in_days: Optional[int] = typer.Option(None, help="Number of days before the invite expires"),
) -> None:
    """Create a new invite token."""

    engine = get_engine()
    with Session(engine) as session:
        creator = None
        if username:
            normalized = auth_service.normalize_username(username)
            creator = session.exec(select(User).where(User.username == normalized)).first()
            if not creator:
                typer.echo(f"User '{normalized}' not found.")
                raise typer.Exit(code=1)
            if not creator.is_admin:
                typer.echo(f"User '{normalized}' is not an admin.")
                raise typer.Exit(code=1)

        invite = auth_service.create_invite_token(
            session,
            created_by=creator,
            max_uses=max_uses,
            expires_in_days=expires_in_days,
        )
        typer.echo(f"Invite token: {invite.token}")
        if invite.expires_at:
            typer.echo(f"Expires at: {invite.expires_at.isoformat()}Z")


if __name__ == "__main__":
    cli()
