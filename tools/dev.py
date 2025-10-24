from __future__ import annotations

from typing import Optional

import click
import uvicorn
from sqlmodel import Session, select

from app.db import get_engine, init_db
from app.models import User
from app.services import auth_service


@click.group(help="Developer utilities for the WhiteBalloon project.")
def cli() -> None:
    """Entry point for the CLI group."""


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Interface to bind the development server")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind the development server")
@click.option("--reload/--no-reload", default=True, show_default=True, help="Enable auto-reload on code changes")
def runserver(host: str, port: int, reload: bool) -> None:
    """Start the FastAPI application using uvicorn."""

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, factory=False)


@cli.command(name="init-db")
def init_db_command() -> None:
    """Initialize the local database."""

    init_db()
    click.secho("Database ready.", fg="green")


@cli.command(name="create-admin")
@click.argument("username")
def create_admin(username: str) -> None:
    """Promote an existing user to administrator."""

    engine = get_engine()
    normalized = auth_service.normalize_username(username)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == normalized)).first()
        if not user:
            click.echo(f"User '{normalized}' not found. Register the user first.")
            raise click.Abort()
        user.is_admin = True
        session.commit()
        click.secho(f"User '{normalized}' promoted to admin.", fg="green")


@cli.group(name="session", help="Inspect and manage authentication sessions.")
def session_group() -> None:  # pragma: no cover
    """CLI group for session operations."""


@session_group.command(name="list")
def session_list() -> None:  # pragma: no cover
    """List pending authentication requests (placeholder)."""
    click.echo("Session listing not implemented yet.")


@session_group.command(name="approve")
@click.argument("request_id")
def session_approve(request_id: str) -> None:  # pragma: no cover
    """Approve a pending authentication request (placeholder)."""
    click.echo(f"Request {request_id} approval not implemented yet.")


@session_group.command(name="deny")
@click.argument("request_id")
def session_deny(request_id: str) -> None:  # pragma: no cover
    """Deny a pending authentication request (placeholder)."""
    click.echo(f"Request {request_id} denial not implemented yet.")


@cli.command(name="create-invite")
@click.option("--username", default=None, help="Admin username to attribute the invite to")
@click.option("--max-uses", default=1, show_default=True, type=int, help="Maximum number of times the invite can be used")
@click.option("--expires-in-days", default=None, type=int, help="Number of days before the invite expires")
def create_invite(username: Optional[str], max_uses: int, expires_in_days: Optional[int]) -> None:
    """Create a new invite token."""

    engine = get_engine()
    with Session(engine) as session:
        creator = None
        if username:
            normalized = auth_service.normalize_username(username)
            creator = session.exec(select(User).where(User.username == normalized)).first()
            if not creator:
                click.echo(f"User '{normalized}' not found.")
                raise click.Abort()
            if not creator.is_admin:
                click.echo(f"User '{normalized}' is not an admin.")
                raise click.Abort()

        invite = auth_service.create_invite_token(
            session,
            created_by=creator,
            max_uses=max_uses,
            expires_in_days=expires_in_days,
        )
        click.secho(f"Invite token: {invite.token}", fg="green")
        if invite.expires_at:
            click.echo(f"Expires at: {invite.expires_at.isoformat()}Z")
        click.echo("Claim by visiting /register in the web UI and entering the token, or POST to /auth/register with invite_token.")


if __name__ == "__main__":
    cli()
