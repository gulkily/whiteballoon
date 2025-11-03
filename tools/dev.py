from __future__ import annotations

from typing import Optional
from pathlib import Path

import click
import uvicorn
from sqlalchemy import inspect
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, SQLModel, select

from app.db import get_engine, init_db
from app.config import get_settings
from app.models import AuthRequestStatus, AuthenticationRequest, User, UserSession
from app.modules.requests import services as request_services
from app.services import auth_service
from app.schema_utils import ensure_schema_integrity


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
    """Initialize the local database.

    Creates missing tables if the database already exists; data is not dropped.
    """

    settings = get_settings()
    url = make_url(settings.database_url)

    click.secho("Preparing database initialization", fg="cyan")
    click.echo(f"  URL: {url}")

    # Determine whether the DB already exists (for SQLite) to tailor the message
    pre_existing: Optional[bool] = None
    if url.drivername.startswith("sqlite"):
        db_path = Path(url.database or "data/app.db")
        pre_existing = db_path.exists()
        click.echo(f"  SQLite file: {db_path}")

    try:
        engine = get_engine()
    except Exception as exc:  # pragma: no cover - protective logging
        click.secho("Failed to create database engine.", fg="red", err=True)
        raise click.ClickException(str(exc))

    inspector = inspect(engine)
    metadata_tables = set(SQLModel.metadata.tables.keys())
    existing_tables = set(inspector.get_table_names())

    click.echo(f"  Discovered {len(existing_tables)} existing table(s).")

    try:
        init_db()
    except Exception as exc:  # pragma: no cover - protective logging
        click.secho("Error while creating tables.", fg="red", err=True)
        raise click.ClickException(str(exc))

    refreshed_tables = set(inspect(engine).get_table_names())
    created_tables = sorted(metadata_tables - existing_tables)
    unchanged_tables = sorted(metadata_tables & existing_tables)

    if created_tables:
        click.secho(f"  Created {len(created_tables)} table(s): {', '.join(created_tables)}", fg="green")
    else:
        click.secho("  No new tables were created (all up to date).", fg="yellow")

    click.echo(f"  {len(unchanged_tables)} table(s) already present before initialization.")

    report = ensure_schema_integrity(engine)
    summary = report.summary_counts()
    click.echo("Schema integrity summary:")
    click.echo(
        f"  Tables created during check: {summary['tables_created']} | Columns added: {summary['columns_added']}"
    )
    if summary["mismatches"]:
        click.secho(f"  Column type mismatches detected: {summary['mismatches']}", fg="yellow")
    if summary["warnings"]:
        click.secho(f"  Warnings: {summary['warnings']}", fg="yellow")

    for table in report.tables:
        details: list[str] = []
        if table.created_table:
            details.append("created table")
        if table.added_columns:
            details.append(
                "added columns: " + ", ".join(table.added_columns)
            )
        if table.mismatched_columns:
            mismatch_text = ", ".join(
                f"{name} (expected {expected}, found {actual})"
                for name, expected, actual in table.mismatched_columns
            )
            details.append("type mismatches: " + mismatch_text)
        if table.warnings:
            details.extend(table.warnings)

        if details:
            click.echo(f"  [{table.name}] " + " | ".join(details))

    for error in report.errors:
        click.secho(f"  Error: {error}", fg="red", err=True)

    if report.has_errors:
        raise click.ClickException(
            "Schema integrity check found issues requiring manual attention."
        )

    if pre_existing is True:
        click.secho("Database ready (previously existing) and schema verified.", fg="green")
    elif pre_existing is False:
        click.secho("Database created, verified, and ready.", fg="green")
    else:
        click.secho("Database ready and schema verified.", fg="green")


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
@click.option("--all", "show_all", is_flag=True, help="Include processed requests")
@click.option("--limit", default=20, show_default=True, type=int, help="Maximum rows to display (0 = no limit)")
def session_list(show_all: bool, limit: int) -> None:  # pragma: no cover
    """List authentication requests."""

    engine = get_engine()
    with Session(engine) as session:
        stmt = (
            select(AuthenticationRequest, User.username)
            .join(User, AuthenticationRequest.user_id == User.id)
            .order_by(AuthenticationRequest.created_at.desc())
        )
        if not show_all:
            stmt = stmt.where(AuthenticationRequest.status == AuthRequestStatus.pending)
        if limit > 0:
            stmt = stmt.limit(limit)

        rows = session.exec(stmt).all()
        if not rows:
            click.echo("No authentication requests found.")
            return

        header = f"{'ID':<36}  {'Username':<20}  {'Status':<10}  {'Created':<19}  {'Expires':<19}  Code"
        click.echo(header)
        click.echo("-" * len(header))
        for request, username in rows:
            created = request.created_at.strftime("%Y-%m-%d %H:%M") if request.created_at else "-"
            expires = request.expires_at.strftime("%Y-%m-%d %H:%M") if request.expires_at else "-"
            click.echo(f"{request.id:<36}  {username:<20}  {request.status.value:<10}  {created:<19}  {expires:<19}  {request.verification_code}")


@session_group.command(name="approve")
@click.argument("request_id")
@click.option("--approver", default=None, help="Username recorded as approver")
def session_approve(request_id: str, approver: Optional[str]) -> None:  # pragma: no cover
    """Approve a pending authentication request."""

    engine = get_engine()
    with Session(engine) as session:
        auth_request = session.get(AuthenticationRequest, request_id)
        if not auth_request:
            click.echo(f"Request {request_id} not found.")
            raise click.Abort()

        if auth_request.status != AuthRequestStatus.pending:
            click.echo(f"Request {request_id} is already {auth_request.status.value}.")
            return

        approver_user = None
        if approver:
            normalized = auth_service.normalize_username(approver)
            approver_user = session.exec(select(User).where(User.username == normalized)).first()
            if not approver_user:
                click.echo(f"Approver '{approver}' not found.")
                raise click.Abort()

        pending_count = len(request_services.list_pending_requests_for_user(session, user_id=auth_request.user_id))
        auth_service.approve_auth_request(session, auth_request=auth_request, approver=approver_user)

        user = session.exec(select(User).where(User.id == auth_request.user_id)).first()
        username = user.username if user else str(auth_request.user_id)
        click.secho(
            f"Approved request {request_id} for user {username}. Promoted {pending_count} pending request(s).",
            fg="green",
        )


@session_group.command(name="deny")
@click.argument("request_id")
def session_deny(request_id: str) -> None:  # pragma: no cover
    """Deny a pending authentication request."""

    engine = get_engine()
    with Session(engine) as session:
        auth_request = session.get(AuthenticationRequest, request_id)
        if not auth_request:
            click.echo(f"Request {request_id} not found.")
            raise click.Abort()

        if auth_request.status != AuthRequestStatus.pending:
            click.echo(f"Request {request_id} is already {auth_request.status.value}.")
            return

        auth_request.status = AuthRequestStatus.denied
        session.add(auth_request)

        sessions = session.exec(
            select(UserSession).where(UserSession.auth_request_id == auth_request.id)
        ).all()
        for record in sessions:
            session.delete(record)

        session.commit()
        click.secho(f"Denied request {request_id}.", fg="yellow")


@cli.command(name="create-invite")
@click.option("--username", default=None, help="Admin username to attribute the invite to")
@click.option("--max-uses", default=1, show_default=True, type=int, help="Maximum number of times the invite can be used")
@click.option("--expires-in-days", default=None, type=int, help="Number of days before the invite expires")
@click.option(
    "--auto-approve/--no-auto-approve",
    default=True,
    show_default=True,
    help="Automatically create a fully authenticated session for registrations using this token.",
)
def create_invite(
    username: Optional[str],
    max_uses: int,
    expires_in_days: Optional[int],
    auto_approve: bool,
) -> None:
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
            auto_approve=auto_approve,
        )
        click.secho(f"Invite token: {invite.token}", fg="green")
        if invite.expires_at:
            click.echo(f"Expires at: {invite.expires_at.isoformat()}Z")
        click.echo(f"Auto-approve registrations: {'yes' if invite.auto_approve else 'no'}")
        click.echo("Claim by visiting /register in the web UI and entering the token, or POST to /auth/register with invite_token.")


if __name__ == "__main__":
    cli()
