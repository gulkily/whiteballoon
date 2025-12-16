from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.env import ensure_env_loaded

ensure_env_loaded()

import click
from sqlmodel import Session

from app.db import get_engine
from app.services import peer_auth_service


@click.group(help="Peer authentication utilities.")
def cli() -> None:  # pragma: no cover - CLI helper
    """Entry point for peer-auth tools."""


@cli.command(name="list")
@click.option("--limit", default=peer_auth_service.DEFAULT_PAGE_LIMIT, show_default=True, type=int)
@click.option("--offset", default=0, show_default=True, type=int)
@click.option("--all-statuses", is_flag=True, help="Include approved/denied sessions instead of only pending ones.")
def list_sessions(limit: int, offset: int, all_statuses: bool) -> None:  # pragma: no cover - manual utility
    """Print the current peer-auth session queue."""

    engine = get_engine()
    pending_only = not all_statuses
    with Session(engine) as session:
        summaries = peer_auth_service.list_peer_auth_sessions(
            session,
            limit=limit,
            offset=offset,
            pending_only=pending_only,
        )
        if not summaries:
            click.echo("No peer-auth sessions found.")
            return

        header = f"{'Request ID':<36}  {'User':<20}  {'Code':<8}  {'Created':<19}  {'Session':<13}  Status"
        click.echo(header)
        click.echo("-" * len(header))
        for summary in summaries:
            created = (
                summary.auth_request_created_at.strftime("%Y-%m-%d %H:%M")
                if summary.auth_request_created_at
                else "-"
            )
            click.echo(
                f"{summary.auth_request_id:<36}  {summary.username:<20}  {summary.verification_code:<8}  "
                f"{created:<19}  {summary.session_id[:12]:<13}  {summary.status.value}"
            )


if __name__ == "__main__":  # pragma: no cover - script entry
    cli()
