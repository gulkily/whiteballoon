from __future__ import annotations

import logging
import tarfile
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.hub.config import HubSettings, get_settings, hash_token, persist_peer, reset_settings_cache
from app.hub.pending import get_pending_key, list_pending_keys, remove_pending_key
from app.hub.storage import (
    build_metadata,
    bundle_exists,
    get_bundle_path,
    read_metadata,
    summarize_bundle,
    write_bundle,
)
from app.hub.feed import ingest_bundle
from app.skins.runtime import register_skin_helpers
from app.sync.signing import MANIFEST_FILENAME, SignatureVerificationError, verify_bundle_signature

ADMIN_COOKIE_NAME = "wb_hub_admin"
ADMIN_SESSION_MAX_AGE = 60 * 60 * 12  # 12 hours

admin_router = APIRouter()
templates = Jinja2Templates(directory="templates")
register_skin_helpers(templates)
logger = logging.getLogger("whiteballoon.hub.admin")


def _load_settings() -> HubSettings:
    # Admin edits often happen out-of-band (CLI or file edits), so bust cache per request.
    reset_settings_cache()
    return get_settings()


def _current_admin(request: Request, settings: HubSettings):
    cookie_value = request.cookies.get(ADMIN_COOKIE_NAME)
    if not cookie_value:
        return None
    return settings.admin_for_hash(cookie_value)


def _render_disabled_page(request: Request, settings: HubSettings):
    config_path = str(settings.config_path) if settings.config_path else "Unknown"
    context = {
        "request": request,
        "config_path": config_path,
    }
    return templates.TemplateResponse("hub/admin_disabled.html", context)


def _render_login_page(request: Request, error: bool):
    context = {
        "request": request,
        "show_error": error,
    }
    return templates.TemplateResponse("hub/admin_login.html", context)


def _gather_peer_stats(settings: HubSettings) -> tuple[list[dict], int, int]:
    rows: list[dict] = []
    total_files = 0
    total_bytes = 0
    for peer in sorted(settings.peers.values(), key=lambda p: p.name.lower()):
        bundle_root = get_bundle_path(settings, peer)
        has_bundle = bundle_exists(settings, peer)
        metadata = read_metadata(settings, peer) or {}
        summary = summarize_bundle(bundle_root) if has_bundle else {"file_count": 0, "total_bytes": 0}
        total_files += summary["file_count"]
        total_bytes += summary["total_bytes"]
        rows.append(
            {
                "name": peer.name,
                "has_bundle": has_bundle,
                "file_count": summary["file_count"],
                "size_kb": summary["total_bytes"] // 1024,
                "signed_at": metadata.get("signed_at", "—"),
                "digest": metadata.get("manifest_digest", "—"),
                "public_key_short": f"…{peer.public_key[-16:]}" if peer.public_key else "—",
            }
        )
    return rows, total_files, total_bytes


def _extract_saved_bundle(archive_path: Path, tmp_dir: Path) -> Path:
    if not archive_path.exists():
        raise FileNotFoundError(f"Pending archive missing: {archive_path}")
    extraction_root = tmp_dir / "bundle"
    extraction_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError("Pending bundle contains unsafe paths")
        tar.extractall(path=extraction_root)
    manifest = next(extraction_root.rglob(MANIFEST_FILENAME), None)
    if not manifest:
        raise RuntimeError("Manifest missing from pending bundle")
    return manifest.parent


def _replay_pending_bundle(pending, peer, settings: HubSettings) -> None:
    if not peer:
        raise RuntimeError("Peer missing for replay")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bundle_root = _extract_saved_bundle(pending.bundle_path, tmp_path)
        metadata = verify_bundle_signature(bundle_root)
        if metadata.public_key_b64 != pending.presented_key:
            raise SignatureVerificationError("Pending bundle signed by unexpected key")
        hub_metadata = build_metadata(peer, metadata.manifest_digest, metadata.signed_at)
        write_bundle(settings, peer, bundle_root, hub_metadata)
        stored_bundle = get_bundle_path(settings, peer)
        ingest_bundle(
            stored_bundle,
            peer_name=peer.name,
            manifest_digest=metadata.manifest_digest,
            signed_at=metadata.signed_at,
        )


def _build_pending_entries(settings: HubSettings) -> list[dict[str, object]]:
    entries = []
    for item in list_pending_keys():
        peer = settings.get_peer(item.peer_name)
        entries.append(
            {
                "id": item.id,
                "peer_name": item.peer_name,
                "presented_key": item.presented_key,
                "created_at": item.created_at,
                "manifest_digest": item.manifest_digest,
                "signed_at": item.signed_at,
                "existing_keys": list(peer.public_keys) if peer else [],
                "peer_missing": peer is None,
            }
        )
    return entries


def _render_dashboard(
    request: Request,
    settings: HubSettings,
    admin_name: str,
    notice: str | None = None,
    error: str | None = None,
):
    peer_rows, total_files, total_bytes = _gather_peer_stats(settings)
    pending_entries = _build_pending_entries(settings)
    context = {
        "request": request,
        "admin_name": admin_name,
        "config_path": str(settings.config_path) if settings.config_path else "Unknown",
        "storage_dir": str(settings.storage_dir),
        "allow_auto_register_push": settings.allow_auto_register_push,
        "allow_auto_register_pull": settings.allow_auto_register_pull,
        "peer_rows": peer_rows,
        "peer_count": len(peer_rows),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_kb": total_bytes // 1024,
        "pending_entries": pending_entries,
        "notice": notice,
        "error_message": error,
    }
    return templates.TemplateResponse("hub/admin_dashboard.html", context)


@admin_router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return _render_disabled_page(request, settings)
    admin = _current_admin(request, settings)
    if not admin:
        error = request.query_params.get("error") == "invalid"
        return _render_login_page(request, error)
    notice = request.query_params.get("notice")
    error_msg = request.query_params.get("flash_error")
    return _render_dashboard(request, settings, admin_name=admin.name, notice=notice, error=error_msg)


@admin_router.post("/admin/login")
async def admin_login(
    request: Request,
    token: str = Form(...),
):
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    token_hash = hash_token(token)
    admin = settings.admin_for_hash(token_hash)
    if not admin:
        response = RedirectResponse(url="/admin?error=invalid", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(ADMIN_COOKIE_NAME)
        return response
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    secure_cookie = request.url.scheme == "https"
    response.set_cookie(
        ADMIN_COOKIE_NAME,
        token_hash,
        max_age=ADMIN_SESSION_MAX_AGE,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
    )
    return response


@admin_router.post("/admin/logout")
async def admin_logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response


def _redirect_with_notice(path: str) -> RedirectResponse:
    return RedirectResponse(url=path, status_code=status.HTTP_303_SEE_OTHER)


@admin_router.post("/admin/pending/{entry_id}/approve")
async def approve_pending_key(request: Request, entry_id: str):
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return _render_disabled_page(request, settings)
    admin = _current_admin(request, settings)
    if not admin:
        return _redirect_with_notice("/admin?error=invalid")
    pending = get_pending_key(entry_id)
    if not pending:
        return _redirect_with_notice("/admin?notice=pending-missing")
    peer = settings.get_peer(pending.peer_name)
    if not peer:
        remove_pending_key(entry_id)
        logger.warning("Pending key %s references missing peer '%s'", entry_id, pending.peer_name)
        return _redirect_with_notice("/admin?notice=peer-missing")
    updated_peer = peer
    if not peer.allows_public_key(pending.presented_key):
        if not settings.config_path:
            logger.error("Cannot persist peer '%s': config path missing", peer.name)
            return _redirect_with_notice("/admin?flash_error=config-missing")
        updated_peer = peer.append_public_key(pending.presented_key)
        persist_peer(
            settings.config_path,
            updated_peer,
            storage_dir=settings.storage_dir,
            allow_push=settings.allow_auto_register_push,
            allow_pull=settings.allow_auto_register_pull,
        )
        logger.info(
            "Admin %s approved new key for peer '%s' (pending %s)",
            admin.name,
            peer.name,
            entry_id,
        )
    else:
        logger.info("Admin %s reprocessed existing key for peer '%s'", admin.name, peer.name)

    fresh_settings = _load_settings()
    fresh_peer = fresh_settings.get_peer(pending.peer_name)
    try:
        _replay_pending_bundle(pending, fresh_peer, fresh_settings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pending bundle replay failed for peer '%s'", pending.peer_name)
        return _redirect_with_notice("/admin?flash_error=replay-failed")

    remove_pending_key(entry_id)
    return _redirect_with_notice("/admin?notice=key-approved")


@admin_router.post("/admin/pending/{entry_id}/discard")
async def discard_pending_key(request: Request, entry_id: str):
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return _render_disabled_page(request, settings)
    admin = _current_admin(request, settings)
    if not admin:
        return _redirect_with_notice("/admin?error=invalid")
    pending = get_pending_key(entry_id)
    if pending:
        logger.info("Admin %s discarded pending key for peer '%s' (%s)", admin.name, pending.peer_name, entry_id)
    remove_pending_key(entry_id)
    return _redirect_with_notice("/admin?notice=pending-discarded")


__all__ = ["admin_router"]
