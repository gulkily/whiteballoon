from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Annotated, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlmodel import select

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import (
    HELP_REQUEST_STATUS_DRAFT,
    HelpRequest,
    InviteToken,
    RequestComment,
    User,
    UserSession,
)
from app.routes.ui.helpers import describe_session_role, templates
from app.security.csrf import generate_csrf_token, validate_csrf_token
from app.sync import job_tracker
from app.sync.activity_log import append_event, read_events
from app.sync.peer_status import collect_peer_statuses
from app.sync.peers import Peer, load_peers, save_peers
from app.sync.pending_pull import list_pending_pulls, get_pending_pull, remove_pending_pull, approve_pending_pull
from app.sync.signing import (
    MANIFEST_FILENAME,
    PUBLIC_KEYS_DIRNAME,
    SIGNATURE_FILENAME,
    SignatureVerificationError,
    load_keypair,
    verify_bundle_signature,
)

router = APIRouter(tags=["ui"])
logger = logging.getLogger(__name__)


SYNC_SCOPE_VALUES = {"private", "public"}
SYNC_SCOPE_MODELS = {
    "request": HelpRequest,
    "comment": RequestComment,
    "user": User,
    "invite": InviteToken,
}


def _default_peer_form_values(name: str = "") -> dict[str, str]:
    return {
        "name": name,
        "path": "",
        "url": "",
        "token": "",
        "public_key": "",
    }


def _serialize_peer_form(peer: Peer) -> dict[str, str]:
    values = _default_peer_form_values(peer.name)
    values.update(
        {
            "path": peer.path.as_posix() if isinstance(peer.path, Path) else (peer.path or ""),
            "url": peer.url or "",
            "token": peer.token or "",
            "public_key": peer.public_key or "",
        }
    )
    return values


def _normalize_field(value: Optional[str]) -> str:
    return (value or "").strip()


def _normalize_public_key_input(value: Optional[str]) -> Optional[str]:
    cleaned = _normalize_field(value)
    if not cleaned:
        return None
    return "".join(cleaned.split())


def _coerce_path(value: str) -> Optional[Path]:
    cleaned = _normalize_field(value)
    if not cleaned:
        return None
    return Path(cleaned).expanduser()


def _validate_peer_payload(
    *,
    name: str,
    path: str,
    url: str,
    token: str,
    existing_names: set[str],
    editing: bool = False,
) -> list[str]:
    errors: list[str] = []
    normalized_name = name.strip()
    if not editing:
        if not normalized_name:
            errors.append("Enter a peer name.")
        elif not re.fullmatch(r"[a-zA-Z0-9_-]+", normalized_name):
            errors.append("Peer names may contain letters, numbers, hyphens, and underscores only.")
        elif normalized_name in existing_names:
            errors.append(f"Peer '{normalized_name}' already exists.")

    has_path = bool(path)
    has_url = bool(url)
    if not has_path and not has_url:
        errors.append("Provide a filesystem path or hub URL.")

    if has_url and not url.startswith(("http://", "https://")):
        errors.append("Hub URLs must start with http:// or https://.")

    if has_url and not token:
        errors.append("Hub peers require a bearer token.")

    return errors


def _load_peer_or_404(peer_name: str) -> Peer:
    peers = load_peers()
    for peer in peers:
        if peer.name == peer_name:
            return peer
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")


def _require_admin_session(session_user: SessionUser) -> None:
    if not session_user.user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def _ensure_csrf(session: UserSession, token: str) -> None:
    if not validate_csrf_token(session.id, token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid form token")


def _redirect_to_sync_control(request: Request, message: Optional[str], tone: str = "info") -> Response:
    url = request.url_for("sync_control_center")
    if message:
        params = urlencode({"peer_message": message, "peer_message_tone": tone})
        url = f"{url}?{params}"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


_TOOLS_MODULE: ModuleType | None = None


def _load_tools_module() -> ModuleType:
    global _TOOLS_MODULE
    if _TOOLS_MODULE is not None:
        return _TOOLS_MODULE

    project_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(project_root))
    spec = importlib.util.spec_from_file_location("wb_tools_dev", project_root / "tools" / "dev.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load tools.dev module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _TOOLS_MODULE = module
    return module


def _run_push_job(peer_name: str, triggered_by: str | None = None) -> None:
    logger.info("Starting push job for peer '%s'", peer_name)
    job_tracker.mark_started(peer_name, "push")
    tools_dev = _load_tools_module()
    PendingApprovalError = getattr(tools_dev, "PendingApprovalError", None)
    try:
        tools_dev.sync_push.callback(peer_name)
        job_tracker.mark_finished(peer_name, "push", True, "Push completed successfully")
        append_event(peer=peer_name, action="push", status="success", triggered_by=triggered_by)
    except Exception as exc:  # noqa: BLE001
        if PendingApprovalError and isinstance(exc, PendingApprovalError):
            message = str(exc)
            logger.info("Push job for peer '%s' pending approval: %s", peer_name, message)
            job_tracker.mark_finished(peer_name, "push", False, message)
            append_event(peer=peer_name, action="push", status="pending", triggered_by=triggered_by, message=message)
        else:
            logger.exception("Push job for peer '%s' failed", peer_name)
            job_tracker.mark_finished(peer_name, "push", False, str(exc))
            append_event(peer=peer_name, action="push", status="error", triggered_by=triggered_by, message=str(exc))


def _run_pull_job(peer_name: str, allow_unsigned: bool, triggered_by: str | None = None) -> None:
    logger.info("Starting pull job for peer '%s'", peer_name)
    job_tracker.mark_started(peer_name, "pull")
    tools_dev = _load_tools_module()
    PendingPullApprovalError = getattr(tools_dev, "PendingPullApprovalError", None)
    try:
        tools_dev.sync_pull.callback(peer_name, allow_unsigned=allow_unsigned)
        job_tracker.mark_finished(peer_name, "pull", True, "Pull completed successfully")
        append_event(peer=peer_name, action="pull", status="success", triggered_by=triggered_by)
    except Exception as exc:  # noqa: BLE001
        if PendingPullApprovalError and isinstance(exc, PendingPullApprovalError):
            message = str(exc)
            logger.info("Pull job for peer '%s' pending approval: %s", peer_name, message)
            job_tracker.mark_finished(peer_name, "pull", False, message)
            append_event(peer=peer_name, action="pull", status="pending", triggered_by=triggered_by, message=message)
        else:
            logger.exception("Pull job for peer '%s' failed", peer_name)
            job_tracker.mark_finished(peer_name, "pull", False, str(exc))
            append_event(peer=peer_name, action="pull", status="error", triggered_by=triggered_by, message=str(exc))


def _build_sync_control_context(
    request: Request,
    session_user: SessionUser,
    *,
    add_form_values: Optional[dict[str, str]] = None,
    add_form_errors: Optional[list[str]] = None,
    edit_form_errors: Optional[dict[str, list[str]]] = None,
    banner_message: Optional[str] = None,
    banner_tone: str = "info",
) -> dict[str, object]:
    user = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(user, session_record)
    add_values = add_form_values or _default_peer_form_values()
    edit_errors = edit_form_errors or {}

    peer_statuses = collect_peer_statuses()
    peers = load_peers()
    peer_forms = [_serialize_peer_form(peer) for peer in peers]
    csrf_token = generate_csrf_token(session_record.id)

    return {
        "request": request,
        "user": user,
        "session": session_record,
        "session_role": session_role,
        "session_username": user.username,
        "session_avatar_url": session_user.avatar_url,
        "peer_statuses": peer_statuses,
        "peer_forms": peer_forms,
        "add_peer_form": add_values,
        "add_peer_errors": add_form_errors or [],
        "edit_peer_errors": edit_errors,
        "peer_banner_message": banner_message,
        "peer_banner_tone": banner_tone,
        "csrf_token": csrf_token,
        "job_statuses": job_tracker.snapshot(),
        "activity_events": read_events(limit=20),
        "pending_pull_entries": list_pending_pulls(),
    }


@router.get("/admin/sync-control")
def sync_control_center(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    banner_message = request.query_params.get("peer_message")
    banner_tone = request.query_params.get("peer_message_tone", "info")
    context = _build_sync_control_context(
        request,
        session_user,
        banner_message=banner_message,
        banner_tone=banner_tone,
    )
    return templates.TemplateResponse("sync/control.html", context)


@router.post("/admin/sync-control/peers/add")
def sync_control_add_peer(
    request: Request,
    name: Annotated[str, Form(...)],
    csrf_token: Annotated[str, Form(...)],
    path: Annotated[Optional[str], Form()] = None,
    url: Annotated[Optional[str], Form()] = None,
    token: Annotated[Optional[str], Form()] = None,
    public_key: Annotated[Optional[str], Form()] = None,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    add_form_values = {
        "name": _normalize_field(name),
        "path": _normalize_field(path),
        "url": _normalize_field(url),
        "token": _normalize_field(token),
        "public_key": _normalize_field(public_key),
    }

    peers = load_peers()
    existing_names = {peer.name for peer in peers}
    errors = _validate_peer_payload(
        name=add_form_values["name"],
        path=add_form_values["path"],
        url=add_form_values["url"],
        token=add_form_values["token"],
        existing_names=existing_names,
        editing=False,
    )
    if errors:
        context = _build_sync_control_context(
            request,
            session_user,
            add_form_values=add_form_values,
            add_form_errors=errors,
        )
        return templates.TemplateResponse("sync/control.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    new_peer = Peer(
        name=add_form_values["name"],
        path=_coerce_path(add_form_values["path"]),
        url=add_form_values["url"] or None,
        token=add_form_values["token"] or None,
        public_key=_normalize_public_key_input(add_form_values["public_key"]),
    )
    peers.append(new_peer)
    save_peers(peers)
    logger.info("Admin %s added sync peer '%s'", session_user.user.username, new_peer.name)
    return _redirect_to_sync_control(request, f"Peer '{new_peer.name}' added.", tone="success")


@router.post("/admin/sync-control/peers/{peer_name}/edit")
def sync_control_edit_peer(
    peer_name: str,
    request: Request,
    csrf_token: Annotated[str, Form(...)],
    path: Annotated[Optional[str], Form()] = None,
    url: Annotated[Optional[str], Form()] = None,
    token: Annotated[Optional[str], Form()] = None,
    public_key: Annotated[Optional[str], Form()] = None,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    peers = load_peers()
    target = next((peer for peer in peers if peer.name == peer_name), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer not found")

    form_values = _default_peer_form_values(peer_name)
    form_values.update(
        {
            "path": _normalize_field(path),
            "url": _normalize_field(url),
            "token": _normalize_field(token),
            "public_key": _normalize_field(public_key),
        }
    )

    existing_names = {peer.name for peer in peers if peer.name != peer_name}
    errors = _validate_peer_payload(
        name=peer_name,
        path=form_values["path"],
        url=form_values["url"],
        token=form_values["token"],
        existing_names=existing_names,
        editing=True,
    )
    if errors:
        context = _build_sync_control_context(
            request,
            session_user,
            edit_form_errors={peer_name: errors},
        )
        return templates.TemplateResponse("sync/control.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    target.path = _coerce_path(form_values["path"])
    target.url = form_values["url"] or None
    target.token = form_values["token"] or None
    target.public_key = _normalize_public_key_input(form_values["public_key"])
    save_peers(peers)
    logger.info("Admin %s updated sync peer '%s'", session_user.user.username, peer_name)
    return _redirect_to_sync_control(request, f"Peer '{peer_name}' updated.", tone="success")


@router.post("/admin/sync-control/peers/{peer_name}/delete")
def sync_control_delete_peer(
    peer_name: str,
    request: Request,
    csrf_token: Annotated[str, Form(...)],
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    peers = load_peers()
    remaining = [peer for peer in peers if peer.name != peer_name]
    if len(remaining) == len(peers):
        logger.warning("Attempt to remove unknown peer '%s'", peer_name)
        context = _build_sync_control_context(
            request,
            session_user,
            banner_message=f"Peer '{peer_name}' no longer exists.",
            banner_tone="warning",
        )
        return templates.TemplateResponse("sync/control.html", context, status_code=status.HTTP_404_NOT_FOUND)

    save_peers(remaining)
    logger.info("Admin %s removed sync peer '%s'", session_user.user.username, peer_name)
    return _redirect_to_sync_control(request, f"Peer '{peer_name}' removed.", tone="success")


@router.post("/admin/sync-control/peers/{peer_name}/push")
def sync_control_push_peer(
    peer_name: str,
    request: Request,
    background_tasks: BackgroundTasks,
    csrf_token: Annotated[str, Form(...)],
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    _load_peer_or_404(peer_name)
    job_tracker.queue_job(peer_name, "push", triggered_by=session_user.user.username)
    background_tasks.add_task(_run_push_job, peer_name, session_user.user.username)
    return _redirect_to_sync_control(request, f"Push queued for '{peer_name}'.", tone="info")


@router.post("/admin/sync-control/peers/{peer_name}/pull")
def sync_control_pull_peer(
    peer_name: str,
    request: Request,
    background_tasks: BackgroundTasks,
    csrf_token: Annotated[str, Form(...)],
    allow_unsigned: Annotated[Optional[str], Form()] = None,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    _load_peer_or_404(peer_name)
    job_tracker.queue_job(peer_name, "pull", triggered_by=session_user.user.username)
    background_tasks.add_task(_run_pull_job, peer_name, bool(allow_unsigned), session_user.user.username)
    tone = "warning" if allow_unsigned else "info"
    return _redirect_to_sync_control(request, f"Pull queued for '{peer_name}'.", tone=tone)


@router.post("/admin/sync-control/pending-pull/{pending_id}/approve")
def sync_control_approve_pending_pull(
    pending_id: str,
    request: Request,
    csrf_token: Annotated[str, Form(...)],
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    entry = get_pending_pull(pending_id)
    if not entry:
        return _redirect_to_sync_control(request, f"Pending pull '{pending_id}' not found.", tone="error")
    try:
        peer_name, count, key_updated = approve_pending_pull(entry)
    except ValueError as exc:
        return _redirect_to_sync_control(request, str(exc), tone="error")
    message = f"Approved pending pull for '{peer_name}' and imported {count} record(s)."
    if key_updated:
        message += " Trusted key updated."
    logger.info(
        "Admin %s approved pending pull %s for peer '%s'",
        session_user.user.username,
        pending_id,
        peer_name,
    )
    append_event(peer=peer_name, action="pull-approve", status="success", triggered_by=session_user.user.username, message=message)
    return _redirect_to_sync_control(request, message, tone="success")


@router.post("/admin/sync-control/pending-pull/{pending_id}/discard")
def sync_control_discard_pending_pull(
    pending_id: str,
    request: Request,
    csrf_token: Annotated[str, Form(...)],
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    _require_admin_session(session_user)
    _ensure_csrf(session_user.session, csrf_token)
    entry = get_pending_pull(pending_id)
    if entry:
        remove_pending_pull(entry)
        logger.info(
            "Admin %s discarded pending pull %s for peer '%s'",
            session_user.user.username,
            pending_id,
            entry.peer_name,
        )
        message = f"Discarded pending pull '{pending_id}'."
        tone = "success"
    else:
        message = f"Pending pull '{pending_id}' not found."
        tone = "error"
    return _redirect_to_sync_control(request, message, tone=tone)


@router.post("/sync/scope")
def update_sync_scope(
    request: Request,
    entity_type: Annotated[str, Form(...)],
    entity_id: Annotated[int, Form(...)],
    scope: Annotated[str, Form(...)],
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    next_url: Optional[str] = Form(None),
) -> Response:
    user = session_user.user
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    cleaned_scope = scope.lower().strip()
    if cleaned_scope not in SYNC_SCOPE_VALUES:
        cleaned_scope = "private"

    model = SYNC_SCOPE_MODELS.get(entity_type)
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported entity type")

    record = db.get(model, entity_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if getattr(record, "sync_scope", cleaned_scope) != cleaned_scope:
        record.sync_scope = cleaned_scope
        db.add(record)
        db.commit()

    wants_json = "application/json" in (request.headers.get("accept") or "").lower()

    redirect_to = next_url or request.headers.get("referer") or "/"
    if wants_json:
        return JSONResponse(
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "scope": getattr(record, "sync_scope", cleaned_scope),
            }
        )
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/sync/public")
def sync_public(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    user = session_user.user
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    public_requests = db.exec(
        select(HelpRequest)
        .where(HelpRequest.sync_scope == "public")
        .where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
    ).all()
    public_comments = db.exec(select(RequestComment).where(RequestComment.sync_scope == "public")).all()
    public_users = db.exec(select(User).where(User.sync_scope == "public")).all()
    public_invites = db.exec(select(InviteToken).where(InviteToken.sync_scope == "public")).all()

    session_record = session_user.session
    session_role = describe_session_role(user, session_record)

    bundle_dir = Path("data/public_sync")
    manifest_path = bundle_dir / MANIFEST_FILENAME
    signature_path = bundle_dir / SIGNATURE_FILENAME
    public_keys_dir = bundle_dir / PUBLIC_KEYS_DIRNAME
    signature_info: Optional[dict[str, object]] = None
    signature_error: Optional[str] = None
    if manifest_path.exists() and signature_path.exists():
        try:
            metadata = verify_bundle_signature(bundle_dir)
            signature_info = {
                "key_id": metadata.key_id,
                "signed_at": metadata.signed_at,
                "manifest_digest": metadata.manifest_digest,
            }
        except SignatureVerificationError as exc:
            signature_error = str(exc)
    public_key_files: list[dict[str, str]] = []
    if public_keys_dir.exists():
        for path in sorted(public_keys_dir.glob("*.pub")):
            try:
                data = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            record = {
                "rel_path": path.relative_to(bundle_dir).as_posix(),
                "key_id": path.stem,
                "public_key": "",
            }
            for line in data:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                cleaned = value.strip()
                if key.strip().lower() == "key-id" and cleaned:
                    record["key_id"] = cleaned
                if key.strip().lower() == "public-key" and cleaned:
                    record["public_key"] = cleaned
            public_key_files.append(record)

    try:
        local_key = load_keypair()
    except ValueError:
        local_key = None
        if signature_error is None:
            signature_error = "Signing key files are corrupted. Regenerate with 'wb sync keygen --force'."
    keys_dir = Path(".sync/keys")

    context = {
        "request": request,
        "user": user,
        "session": session_record,
        "session_role": session_role,
        "session_username": user.username,
        "session_avatar_url": session_user.avatar_url,
        "public_requests": public_requests,
        "public_comments": public_comments,
        "public_users": public_users,
        "public_invites": public_invites,
        "bundle_dir": bundle_dir,
        "manifest_path": manifest_path,
        "signature_path": signature_path,
        "signature_info": signature_info,
        "signature_error": signature_error,
        "public_key_files": public_key_files,
        "local_signing_key": local_key,
        "keys_dir": keys_dir,
    }
    return templates.TemplateResponse("sync/public.html", context)


__all__ = ["router"]
