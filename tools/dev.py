from __future__ import annotations

from typing import Optional
from pathlib import Path
import shutil
import io
import tarfile
import tempfile
import sys
import json
import os
from datetime import timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.env import ensure_env_loaded

ensure_env_loaded()

import click
import httpx
import uvicorn
from sqlalchemy import inspect
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, SQLModel, select

from app.db import get_engine, init_db
from app.config import get_settings
from app.models import AuthRequestStatus, AuthenticationRequest, User, UserSession
from app.modules.requests import services as request_services
from app.schema_utils import ensure_schema_integrity
from app.services import auth_service, comment_llm_insights_db, vouch_service
from app.url_utils import build_invite_link
from app.sync.export_import import export_sync_data, import_sync_data
from app.sync.peers import Peer, get_peer, load_peers, save_peers
from app.sync.pending_pull import (
    cache_pending_pull,
    list_pending_pulls,
    get_pending_pull,
    approve_pending_pull,
)
from app.sync.signing import (
    SignatureVerificationError,
    SigningKey,
    ensure_local_keypair,
    generate_keypair,
    sign_bundle,
    verify_bundle_signature,
)
from tools.skins_build import (
    BASE_FILENAME,
    BUILD_DIR,
    MANIFEST_FILENAME,
    SKINS_DIR,
    SkinBuildError,
    build_skins,
    discover_skins,
    watch_skins,
)


def running_in_wsl() -> bool:
    """Return True when executing under Windows Subsystem for Linux."""

    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        osrelease = Path("/proc/sys/kernel/osrelease").read_text().lower()
    except FileNotFoundError:
        return False
    return "microsoft" in osrelease


class PendingApprovalError(click.ClickException):
    def __init__(self, peer_name: str, pending_id: str, message: str | None = None) -> None:
        self.peer_name = peer_name
        self.pending_id = pending_id
        detail = message or "Hub queued a pending approval"
        guidance = (
            f"{detail} for peer '{peer_name}'. Pending ID: {pending_id}. "
            "Approve the key via the hub /admin dashboard and retry the push."
        )
        super().__init__(guidance)


class PendingPullApprovalError(click.ClickException):
    def __init__(
        self,
        peer_name: str,
        presented_key: str,
        pending_id: str,
        cache_dir: str | None = None,
    ) -> None:
        self.peer_name = peer_name
        self.presented_key = presented_key
        self.pending_id = pending_id
        self.cache_dir = cache_dir
        guidance = (
            f"Peer '{peer_name}' presented a new key during pull. Pending ID: {pending_id}. "
            "Visit /admin/sync-control or run 'wb sync pull --approve "
            f"{pending_id}' to trust the key and import the cached bundle."
        )
        if cache_dir:
            guidance += f" Cached bundle: {cache_dir}"
        super().__init__(guidance)


@click.group(help="Developer utilities for the WhiteBalloon project.")
def cli() -> None:
    """Entry point for the CLI group."""


@cli.group(name="sync", help="Manual sync utilities")
def sync_group() -> None:
    """Group of sync commands."""


def _ensure_signing_key(auto_generate: bool = True) -> SigningKey:
    keypair, created = ensure_local_keypair(auto_generate=auto_generate)
    if keypair is None:
        raise click.ClickException("Signing key missing. Run 'wb sync keygen'.")
    if created:
        click.secho(
            f"Generated new signing key (id {keypair.key_id}) under .sync/keys.",
            fg="yellow",
        )
    return keypair


def _verify_bundle_dir(bundle_dir: Path, peer: Peer | None, allow_unsigned: bool) -> None:
    expected_key = peer.public_key if peer else None
    try:
        metadata = verify_bundle_signature(bundle_dir, expected_public_key=expected_key)
    except SignatureVerificationError as exc:
        if allow_unsigned:
            click.secho(
                f"Warning: {exc}. Continuing due to --allow-unsigned.",
                fg="yellow",
            )
            return
        raise click.ClickException(str(exc)) from exc
    if expected_key:
        click.secho(
            f"Verified bundle signature for peer '{peer.name}' (key {metadata.key_id}).",
            fg="green",
        )
    else:
        click.secho(
            f"Verified bundle signature (key {metadata.key_id}) but no trusted peer key registered.",
            fg="yellow",
        )


def _print_pending_pull_entries() -> None:
    entries = list_pending_pulls()
    if not entries:
        click.echo("No pending pull approvals.")
        return
    click.secho("Pending pull approvals:", fg="yellow")
    for entry in entries:
        created = entry.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if entry.created_at else "unknown"
        key_hint = entry.presented_key[:16] + "…" if entry.presented_key else "unknown"
        click.echo(f"  ID: {entry.id} | Peer: {entry.peer_name} | Key: {key_hint} | Created: {created}")
    click.echo("Approve with 'wb sync pull --approve <pending-id>' or via the admin UI.")


def _peer_uses_hub(peer: Peer) -> bool:
    return bool(peer.url)


def _ensure_peer_path(peer: Peer) -> Path:
    if peer.path is None:
        raise click.ClickException(
            f"Peer '{peer.name}' is hub-only. Provide a filesystem path or use 'wb sync pull {peer.name}' with a hub URL."
        )
    return peer.path


def _bundle_tarball(bundle_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for file_path in bundle_dir.rglob("*"):
            tar.add(file_path, arcname=file_path.relative_to(bundle_dir))
    buffer.seek(0)
    return buffer.getvalue()


def _hub_endpoint(peer: Peer, suffix: str) -> str:
    if not peer.url:
        raise click.ClickException(f"Peer '{peer.name}' is not configured with a hub URL.")
    base = peer.url.rstrip("/")
    return f"{base}/api/v1/sync/{peer.name}/{suffix.lstrip('/')}"


def _hub_headers(peer: Peer, include_public_key: bool = True) -> dict[str, str]:
    if not peer.token:
        raise click.ClickException(
            f"Peer '{peer.name}' requires a token for hub access. Re-run 'wb sync peers add --token <value>'."
        )
    headers = {"Authorization": f"Bearer {peer.token}"}
    if include_public_key:
        keypair, _ = ensure_local_keypair(auto_generate=True)
        if keypair:
            headers["X-WB-Public-Key"] = keypair.public_key_b64
    return headers


def _push_to_hub(peer: Peer, bundle_dir: Path) -> None:
    payload = _bundle_tarball(bundle_dir)
    url = _hub_endpoint(peer, "bundle")
    headers = _hub_headers(peer)
    click.secho(f"Uploading bundle to hub peer '{peer.name}'...", fg="cyan")
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, files={"bundle": ("bundle.tar.gz", payload, "application/gzip")})
    except httpx.HTTPError as exc:
        raise click.ClickException(f"Hub upload failed: {exc}") from exc
    if response.status_code >= 400:
        detail_text = response.text
        payload_obj: dict | None = None
        pending_detail: dict | None = None
        try:
            payload_obj = response.json()
            detail_obj = payload_obj.get("detail") if isinstance(payload_obj, dict) else None
            if isinstance(detail_obj, dict) and detail_obj.get("error") == "peer_key_mismatch":
                pending_detail = detail_obj
            elif isinstance(detail_obj, str):
                detail_text = detail_obj
        except Exception:
            pass
        if pending_detail:
            pending_id = pending_detail.get("pending_id") or "unknown"
            raise PendingApprovalError(peer.name, str(pending_id), pending_detail.get("message"))
        raise click.ClickException(f"Hub upload failed ({response.status_code}): {detail_text}")
    data = response.json()
    click.secho(
        f"Hub accepted bundle (digest {data.get('manifest_digest')}, files {data.get('stored_files')}).",
        fg="green",
    )


def _pull_from_hub(peer: Peer, temp_root: Path, allow_unsigned: bool) -> Path:
    url = _hub_endpoint(peer, "bundle")
    headers = _hub_headers(peer)
    click.secho(f"Downloading bundle from hub peer '{peer.name}'...", fg="cyan")
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise click.ClickException(f"Hub download failed: {exc}") from exc
    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        raise click.ClickException(f"Hub download failed ({response.status_code}): {detail}")
    tar_path = temp_root / "bundle.tar.gz"
    tar_path.write_bytes(response.content)
    extract_dir = temp_root / "bundle"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_dir)
    metadata = verify_bundle_signature(extract_dir)
    expected_key = peer.public_key if peer else None
    if expected_key and metadata.public_key_b64 != expected_key:
        if allow_unsigned:
            click.secho(
                "Warning: Pull bundle signed with unexpected key but continuing due to --allow-unsigned.",
                fg="yellow",
            )
        else:
            entry = cache_pending_pull(
                peer_name=peer.name,
                bundle_bytes=response.content,
                presented_key=metadata.public_key_b64,
                manifest_digest=metadata.manifest_digest,
                signed_at=metadata.signed_at,
            )
            raise PendingPullApprovalError(
                peer.name,
                metadata.public_key_b64,
                entry.id,
                str(entry.directory),
            )
    if expected_key:
        click.secho(
            f"Verified bundle signature for peer '{peer.name}' (key {metadata.key_id}).",
            fg="green",
        )
    else:
        click.secho(
            f"Verified bundle signature (key {metadata.key_id}) but no trusted peer key registered.",
            fg="yellow",
        )
    return extract_dir


def _update_peer_public_key(peer_name: str, new_key: str) -> Peer:
    peers = load_peers()
    updated: list[Peer] = []
    replaced: Peer | None = None
    for peer in peers:
        if peer.name == peer_name:
            peer = Peer(name=peer.name, path=peer.path, url=peer.url, token=peer.token, public_key=new_key)
            replaced = peer
        updated.append(peer)
    if replaced is None:
        raise click.ClickException(f"Peer '{peer_name}' not found in local registry.")
    save_peers(updated)
    return replaced




@sync_group.command(name="export")
@click.option(
    "--output",
    default="data/public_sync",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory to write .sync.txt files",
)
def sync_export(output: Path) -> None:
    keypair = _ensure_signing_key(auto_generate=True)
    engine = get_engine()
    with Session(engine) as session:
        files = export_sync_data(session, output)
    sig_path = sign_bundle(output, keypair)
    click.secho(f"Wrote {len(files)} files to {output}", fg="green")
    click.secho(f"Signed manifest ({sig_path})", fg="cyan")


@sync_group.command(name="import")
@click.argument("input_dir", type=click.Path(path_type=Path))
@click.option("--peer", "peer_name", default=None, help="Peer entry for signature verification")
@click.option(
    "--allow-unsigned",
    is_flag=True,
    default=False,
    help="Skip signature verification (not recommended)",
)
def sync_import(input_dir: Path, peer_name: str | None, allow_unsigned: bool) -> None:
    peer: Peer | None = None
    if peer_name:
        peer = get_peer(peer_name)
        if not peer:
            raise click.ClickException(f"Peer '{peer_name}' not found. Use 'wb sync peers list'.")
    _ensure_signing_key(auto_generate=True)
    _verify_bundle_dir(input_dir, peer=peer, allow_unsigned=allow_unsigned)
    engine = get_engine()
    with Session(engine) as session:
        count = import_sync_data(session, Path(input_dir))
    click.secho(f"Imported {count} records from {input_dir}", fg="green")


@sync_group.command(name="push")
@click.argument("peer_name")
def sync_push(peer_name: str) -> None:
    peer = get_peer(peer_name)
    if not peer:
        raise click.ClickException(f"Peer '{peer_name}' not found. Use 'wb sync peers add'.")
    keypair = _ensure_signing_key(auto_generate=True)
    engine = get_engine()
    with Session(engine) as session:
        temp_dir = Path("data/public_sync")
        files = export_sync_data(session, temp_dir)
    sign_bundle(temp_dir, keypair)
    if _peer_uses_hub(peer):
        _push_to_hub(peer, temp_dir)
    else:
        dest = _ensure_peer_path(peer)
        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for file in temp_dir.rglob("*"):
            if not file.is_file():
                continue
            rel = file.relative_to(temp_dir)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
            copied += 1
        click.secho(f"Pushed {copied} files (data + signature) to peer '{peer_name}'", fg="green")


@sync_group.command(name="pull")
@click.argument("peer_name", required=False)
@click.option(
    "--allow-unsigned",
    is_flag=True,
    default=False,
    help="Skip signature verification (not recommended)",
)
@click.option("--approve", "pending_id", default=None, help="Approve a pending pull ID")
@click.option("--pending", "show_pending", is_flag=True, help="List pending pull approvals")
def sync_pull(
    peer_name: str | None,
    allow_unsigned: bool,
    pending_id: str | None = None,
    show_pending: bool = False,
) -> None:
    if show_pending:
        _print_pending_pull_entries()
        return
    if pending_id:
        entry = get_pending_pull(pending_id)
        if not entry:
            _print_pending_pull_entries()
            raise click.ClickException(f"Pending pull '{pending_id}' not found.")
        peer_label, count, key_updated = approve_pending_pull(entry)
        message = f"Approved pending pull for peer '{peer_label}' and imported {count} record(s)."
        if key_updated:
            message += " Trusted key updated."
        click.secho(message, fg="green")
        return
    if not peer_name:
        _print_pending_pull_entries()
        raise click.ClickException("Provide a peer name to pull or use --approve/--pending.")
    peer = get_peer(peer_name)
    if not peer:
        raise click.ClickException(f"Peer '{peer_name}' not found. Use 'wb sync peers add'.")
    _ensure_signing_key(auto_generate=True)
    if _peer_uses_hub(peer):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle_dir = _pull_from_hub(peer, tmp_path, allow_unsigned)
            engine = get_engine()
            with Session(engine) as session:
                count = import_sync_data(session, bundle_dir)
    else:
        source = _ensure_peer_path(peer)
        if not source.exists():
            raise click.ClickException(f"Peer path not found: {source}")
        _verify_bundle_dir(source, peer=peer, allow_unsigned=allow_unsigned)
        engine = get_engine()
        with Session(engine) as session:
            count = import_sync_data(session, source)
    click.secho(f"Pulled {count} records from peer '{peer_name}'", fg="green")


@sync_group.command(name="keygen")
@click.option("--force", is_flag=True, default=False, help="Regenerate the signing keypair")
def sync_keygen(force: bool) -> None:
    if force:
        keypair = generate_keypair(force=True)
        click.secho(f"Regenerated signing key (id {keypair.key_id}).", fg="yellow")
    else:
        keypair, created = ensure_local_keypair(auto_generate=True)
        if not keypair:
            raise click.ClickException("Unable to initialize signing keypair.")
        if created:
            click.secho(f"Generated signing key (id {keypair.key_id}).", fg="green")
        else:
            click.secho(f"Signing key already present (id {keypair.key_id}).", fg="cyan")
    click.echo("Public key (share with peers):")
    click.echo(f"  {keypair.public_key_b64}")


@sync_group.group(name="peers")
def peers_group() -> None:
    """Manage peer registry."""


@peers_group.command(name="list")
def peers_list() -> None:
    peers = load_peers()
    if not peers:
        click.echo("No peers configured. Use 'wb sync peers add'.")
        return
    for peer in peers:
        location = peer.url if peer.url else peer.path
        details = f"- {peer.name}: {location}"
        if peer.url:
            details += " [hub]"
        if peer.public_key:
            details += f" (pub={peer.public_key[:16]}...)"
        click.echo(details)


@peers_group.command(name="add")
@click.option("--name", prompt="Peer name")
@click.option("--path", type=click.Path(path_type=Path), default=None, help="Filesystem bundle directory")
@click.option("--url", default=None, help="Hub base URL (e.g., https://hub.example)")
@click.option("--token", default=None, help="Optional auth token")
@click.option(
    "--public-key",
    default=None,
    help="Peer's Ed25519 public key (base64) for signature verification",
)
def peers_add(name: str, path: Path | None, url: str | None, token: str | None, public_key: str | None) -> None:
    peers = load_peers()
    if any(peer.name == name for peer in peers):
        raise click.ClickException(f"Peer '{name}' already exists")
    if not path and not url:
        raise click.ClickException("Provide --path for filesystem peers or --url for hub peers.")
    if url and not token:
        click.secho("Warning: hub peers typically require --token for authentication.", fg="yellow")
    peers.append(Peer(name=name, path=path, url=url, token=token, public_key=public_key))
    save_peers(peers)
    click.secho(f"Added peer '{name}'", fg="green")


@peers_group.command(name="remove")
@click.argument("name")
def peers_remove(name: str) -> None:
    peers = load_peers()
    filtered = [peer for peer in peers if peer.name != name]
    if len(filtered) == len(peers):
        raise click.ClickException(f"Peer '{name}' not found")
    save_peers(filtered)
    click.secho(f"Removed peer '{name}'", fg="green")


@cli.command()
@click.option(
    "--host",
    default=None,
    show_default="127.0.0.1 (WSL auto-switches to 0.0.0.0)",
    help="Interface to bind the development server",
)
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind the development server")
@click.option("--reload/--no-reload", default=True, show_default=True, help="Enable auto-reload on code changes")
def runserver(host: str | None, port: int, reload: bool) -> None:
    """Start the FastAPI application using uvicorn."""

    reload_includes = None
    if reload:
        reload_includes = ["*.py", ".env", ".env.*"]

    effective_host = host or ("0.0.0.0" if running_in_wsl() else "127.0.0.1")
    if host is None and effective_host == "0.0.0.0":
        click.secho(
            "WSL detected; binding to 0.0.0.0 so Windows can reach the dev server via localhost. Use --host to override.",
            fg="yellow",
        )

    uvicorn.run(
        "app.main:app",
        host=effective_host,
        port=port,
        reload=reload,
        reload_includes=reload_includes,
        factory=False,
    )


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

    click.echo("Initializing auxiliary databases...")
    try:
        comment_llm_insights_db.init_db()
    except Exception as exc:  # pragma: no cover - protective logging
        click.secho("  Failed to prepare comment LLM insights DB.", fg="red", err=True)
        raise click.ClickException(str(exc))
    else:
        click.echo(
            f"  comment_llm_insights.db ready at {comment_llm_insights_db.DB_PATH}"
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


@cli.group(name="skins", help="Skin bundle utilities")
def skins_group() -> None:
    """Commands for building and watching skin CSS bundles."""


@skins_group.command(name="build")
@click.option(
    "--output-dir",
    default=str(BUILD_DIR),
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory where compiled skin bundles are written",
)
@click.option(
    "--manifest",
    default=None,
    type=click.Path(path_type=Path),
    help="Optional manifest path (defaults to <output-dir>/manifest.json)",
)
@click.option("--dry-run", is_flag=True, help="List discovered skins without writing bundles")
def skins_build_cli(output_dir: Path, manifest: Path | None, dry_run: bool) -> None:
    try:
        entries = discover_skins()
    except SkinBuildError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        click.secho(f"Discovered {len(entries)} skin(s) in {SKINS_DIR}:", fg="cyan")
        for entry in entries:
            click.echo(f"  - {entry.name} ({entry.path})")
        return

    manifest_path = manifest or (output_dir / MANIFEST_FILENAME)
    try:
        manifest_data = build_skins(skins=entries, output_dir=output_dir, manifest_path=manifest_path)
    except SkinBuildError as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"Built {len(manifest_data)} skin bundle(s) in {output_dir}", fg="green")
    for name, meta in manifest_data.items():
        click.echo(f"  - {name}: {meta['filename']}")
    click.echo(f"Manifest: {manifest_path}")


@skins_group.command(name="watch")
@click.option(
    "--output-dir",
    default=str(BUILD_DIR),
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory where compiled skin bundles are written",
)
@click.option(
    "--manifest",
    default=None,
    type=click.Path(path_type=Path),
    help="Optional manifest path (defaults to <output-dir>/manifest.json)",
)
@click.option("--interval", default=1.0, show_default=True, type=float, help="Polling interval in seconds")
def skins_watch_cli(output_dir: Path, manifest: Path | None, interval: float) -> None:
    manifest_path = manifest or (output_dir / MANIFEST_FILENAME)

    def _log(message: str) -> None:
        click.echo(f"[skins] {message}")

    click.secho(f"Watching {SKINS_DIR} for changes (interval {interval}s)...", fg="cyan")
    try:
        watch_skins(
            interval=interval,
            base_css_path=SKINS_DIR / BASE_FILENAME,
            output_dir=output_dir,
            manifest_path=manifest_path,
            log=_log,
        )
    except SkinBuildError as exc:
        raise click.ClickException(str(exc)) from exc


@skins_group.command(name="list")
def skins_list_cli() -> None:
    """List discovered skins without building bundles."""

    try:
        entries = discover_skins()
    except SkinBuildError as exc:
        raise click.ClickException(str(exc)) from exc

    click.secho(f"Discovered {len(entries)} skin(s) in {SKINS_DIR}:", fg="cyan")
    for entry in entries:
        try:
            rel_path = entry.path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = entry.path
        click.echo(f"  - {entry.name} ({rel_path})")


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
        click.echo(f"Invite link: {build_invite_link(invite.token)}")
        if invite.expires_at:
            click.echo(f"Expires at: {invite.expires_at.isoformat()}Z")
        click.echo(f"Auto-approve registrations: {'yes' if invite.auto_approve else 'no'}")
        click.echo("Claim by visiting /register in the web UI and entering the token, or POST to /auth/register with invite_token.")


if __name__ == "__main__":
    cli()
