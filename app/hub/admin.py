from __future__ import annotations

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.hub.config import HubSettings, get_settings, hash_token, reset_settings_cache
from app.hub.storage import bundle_exists, get_bundle_path, read_metadata, summarize_bundle

ADMIN_COOKIE_NAME = "wb_hub_admin"
ADMIN_SESSION_MAX_AGE = 60 * 60 * 12  # 12 hours

admin_router = APIRouter()
templates = Jinja2Templates(directory="templates")


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


def _render_dashboard(request: Request, settings: HubSettings, admin_name: str):
    peer_rows, total_files, total_bytes = _gather_peer_stats(settings)
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
    return _render_dashboard(request, settings, admin_name=admin.name)


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


__all__ = ["admin_router"]
