from __future__ import annotations

import asyncio
import logging
import json
from datetime import datetime
import csv
import io
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlmodel import select

from app.dependencies import SessionDep, SessionUser, get_session, require_session_user
from app.models import HelpRequest, InviteToken, User
from app import config
from app.routes.ui.helpers import friendly_time
from app.dedalus.logging import finalize_logged_run, start_logged_run
from app.dedalus import log_store

try:
    from dedalus_labs import AsyncDedalus, DedalusRunner
except ImportError:  # pragma: no cover - optional dependency
    AsyncDedalus = None  # type: ignore
    DedalusRunner = None  # type: ignore
from app.realtime import (
    enqueue_job as enqueue_realtime_job,
    load_job_history as realtime_load_history,
    update_job as update_realtime_job,
)
from app.routes.ui.helpers import describe_session_role, templates
from app.services import (
    comment_llm_insights_service,
    member_directory_service,
    request_comment_service,
    user_attribute_service,
    user_profile_highlight_service,
)
from starlette.datastructures import URL

router = APIRouter(tags=["ui"])
PAGE_SIZE = 25
ENV_PATH = Path(".env")
ENV_EXAMPLE_PATH = Path(".env.example")
DEDALUS_ENV_KEY = "DEDALUS_API_KEY"
DEDALUS_ENV_VERIFIED = "DEDALUS_API_KEY_VERIFIED_AT"
VERIFICATION_MAX_CHARS = 300
DEDALUS_VERIFICATION_PROMPT = (
    "You are verifying the WhiteBalloon Mutual Aid Copilot Dedalus connection. "
    "Respond with exactly one line under {max_chars} characters. "
    "Format: `OK: <short summary>; tools: <comma-separated tools>` when healthy. "
    "If anything fails, respond `ERROR: <concise reason>` and optionally append minimal guidance. "
    "Explicitly mention that you recognize the WhiteBalloon context and list the MCP tools available "
    "(for example audit_auth_requests) even if you do not call them. Do not provide multi-step checklists."
).format(max_chars=VERIFICATION_MAX_CHARS)

STATUS_PATTERN = re.compile(r"^(OK|ERROR):\s*(.+)", re.IGNORECASE)
TOOLS_PATTERN = re.compile(r";\s*tools?\s*:\s*(.+)", re.IGNORECASE)
DEDALUS_SCOPE = "dedalus"
DEDALUS_VERIFY_ACTION = "dedalus-verify"
DEDALUS_SAVE_ACTION = "dedalus-save"
logger = logging.getLogger(__name__)


def parse_verification_response(text: str | None) -> tuple[str | None, str | None, list[str]]:
    if not text:
        return None, None, []
    match = STATUS_PATTERN.match(text.strip())
    if not match:
        return None, text.strip(), []
    label = match.group(1).upper()
    remainder = match.group(2)
    tools: list[str] = []
    tools_match = TOOLS_PATTERN.search(remainder)
    if tools_match:
        tools_text = tools_match.group(1)
        remainder = remainder[: tools_match.start()].strip()
        tokens: list[str] = []
        for section in tools_text.split(";"):
            for chunk in section.split(","):
                value = chunk.strip()
                if value:
                    tokens.append(value)
        tools = tokens
    summary = remainder.strip()
    return label, summary, tools


def _require_admin(session_user: SessionUser) -> None:
    if not session_user.user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_account_avatar(db: SessionDep, user_id: int) -> Optional[str]:
    return user_attribute_service.get_attribute(
        db,
        user_id=user_id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )


@router.get("/admin")
def admin_panel(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    viewer = session_user.user
    session = session_user.session

    admin_links = [
        {
            "title": "Profile directory",
            "description": "Audit every local account, review contact info, and drill into individual activity.",
            "href": "/admin/profiles",
        },
        {
            "title": "Sync dashboard",
            "description": "Review public sharing scope, bundle signatures, and trigger manual exports.",
            "href": "/sync/public",
        },
        {
            "title": "Dedalus integration",
            "description": "Manage the API key that powers the Mutual Aid Copilot.",
            "href": "/admin/dedalus",
        },
        {
            "title": "Dedalus activity",
            "description": "Review prompts, responses, and MCP tool calls for every Dedalus run.",
            "href": "/admin/dedalus/logs",
        },
        {
            "title": "Comment insights",
            "description": "Browse LLM-generated summaries/tags for request comments.",
            "href": "/admin/comment-insights",
        },
    ]

    context = {
        "request": request,
        "user": viewer,
        "session": session,
        "session_role": describe_session_role(viewer, session),
        "session_username": viewer.username,
        "session_avatar_url": _get_account_avatar(db, viewer.id),
        "admin_links": admin_links,
    }
    return templates.TemplateResponse("admin/panel.html", context)

def _ensure_env_file() -> None:
    if ENV_PATH.exists():
        return
    if ENV_EXAMPLE_PATH.exists():
        ENV_PATH.write_text(ENV_EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        ENV_PATH.touch()


def _write_env_value(key: str, value: Optional[str]) -> None:
    _ensure_env_file()
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            found = True
            if value is not None:
                updated.append(f"{key}={value}")
            continue
        updated.append(line)
    if value is not None and not found:
        if updated and updated[-1].strip() != "":
            updated.append("")
        updated.append(f"{key}={value}")
    # Remove trailing blank lines
    while updated and updated[-1] == "":
        updated.pop()
    content = "\n".join(updated)
    if content:
        content += "\n"
    ENV_PATH.write_text(content, encoding="utf-8")


async def _verify_dedalus_api_key(value: str) -> tuple[bool, str]:
    if not value:
        return False, "No API key configured."
    if AsyncDedalus is None or DedalusRunner is None:
        return False, "Install the 'dedalus-labs' SDK to enable verification."
    try:
        client = AsyncDedalus(api_key=value)  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - backwards compatibility
        os.environ[DEDALUS_ENV_KEY] = value
        client = AsyncDedalus()  # type: ignore[call-arg]
    runner = DedalusRunner(client)  # type: ignore[call-arg]
    instructions = DEDALUS_VERIFICATION_PROMPT
    run_id = start_logged_run(
        user_id=None,
        entity_type="admin",
        entity_id="dedalus-key-check",
        model="openai/gpt-5-mini",
        prompt=instructions,
    )
    try:
        response = await runner.run(
            input=instructions,
            model="openai/gpt-5-mini",
        )
    except Exception as exc:  # pragma: no cover - external dependency
        finalize_logged_run(
            run_id=run_id,
            response=None,
            status="error",
            error=str(exc),
            structured_label="ERROR",
        )
        return False, str(exc)
    raw_text = getattr(response, "final_output", None)
    if not raw_text and hasattr(response, "outputs"):
        raw_text = str(response.outputs)
    message = raw_text or "Verified successfully."
    label, summary, tools = parse_verification_response(raw_text)
    finalize_logged_run(
        run_id=run_id,
        response=message,
        status="success",
        structured_label=label,
        structured_tools=tools,
    )
    display = summary or message
    return True, display


def _serialize_run(record: log_store.RunRecord) -> dict:
    return {
        "run_id": record.run_id,
        "created_at": record.created_at,
        "completed_at": record.completed_at,
        "user_id": record.user_id,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "model": record.model,
        "prompt": record.prompt,
        "response": record.response,
        "status": record.status,
        "error": record.error,
        "context_hash": record.context_hash,
        "tool_calls": record.tool_calls,
    }


def _dedalus_filters(
    *,
    user_id: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[str],
    status: Optional[str],
    limit: int,
) -> dict:
    return {
        "user_id": user_id or "",
        "entity_type": entity_type or "",
        "entity_id": entity_id or "",
        "status": status or "",
        "limit": limit,
    }


def _queue_dedalus_job(action: str, triggered_by: str, *, message: Optional[str] = None):
    return enqueue_realtime_job(
        category=f"dedalus.{action}",
        target={"scope": DEDALUS_SCOPE, "action": action},
        triggered_by=triggered_by,
        message=message or "Job queued",
    )


async def _run_dedalus_job(job_id: str, *, api_key: str, action: str) -> None:
    try:
        update_realtime_job(job_id, state="running", message="Contacting Dedalus Labs…")
        success, note = await _verify_dedalus_api_key(api_key)
        final_state = "success" if success else "error"
        if success:
            timestamp = datetime.utcnow().isoformat()
            _write_env_value(DEDALUS_ENV_VERIFIED, timestamp)
            os.environ[DEDALUS_ENV_VERIFIED] = timestamp
        elif action == DEDALUS_SAVE_ACTION:
            _write_env_value(DEDALUS_ENV_VERIFIED, None)
            os.environ.pop(DEDALUS_ENV_VERIFIED, None)
        update_realtime_job(job_id, state=final_state, message=note)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Dedalus %s job failed", action)
        update_realtime_job(job_id, state="error", message=str(exc))
    finally:
        config.reset_settings_cache()


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _snapshot_to_template_job(snapshot: Optional[dict]) -> Optional[dict]:
    if not snapshot:
        return None
    return {
        "job_id": snapshot.get("id"),
        "status": snapshot.get("state") or "queued",
        "message": snapshot.get("message"),
        "queued_at": _parse_iso_datetime(snapshot.get("queued_at")),
        "started_at": _parse_iso_datetime(snapshot.get("started_at")),
        "finished_at": _parse_iso_datetime(snapshot.get("finished_at")),
    }


def _dedalus_job_statuses() -> dict[str, Optional[dict]]:
    snapshots = realtime_load_history(limit=200)
    latest: dict[str, dict] = {}
    for snapshot in reversed(snapshots):
        category = str(snapshot.get("category") or "")
        if not category.startswith("dedalus."):
            continue
        target = snapshot.get("target") or {}
        action = target.get("action")
        if not action or action in latest:
            continue
        latest[action] = snapshot
        if len(latest) >= 2:
            break
    return {
        DEDALUS_VERIFY_ACTION: _snapshot_to_template_job(latest.get(DEDALUS_VERIFY_ACTION)),
        DEDALUS_SAVE_ACTION: _snapshot_to_template_job(latest.get(DEDALUS_SAVE_ACTION)),
    }


@router.get("/admin/dedalus/logs")
def admin_dedalus_logs(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
    user_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    message: Optional[str] = Query(None),
    severity: Optional[str] = Query("success"),
):
    _require_admin(session_user)
    runs = log_store.fetch_runs(
        limit=limit,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
    )
    settings = config.get_settings()
    context = {
        "request": request,
        "user": session_user.user,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "entries": [_serialize_run(run) for run in runs],
        "filters": _dedalus_filters(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            limit=limit,
        ),
        "flash_message": message,
        "flash_severity": severity,
        "retention_days": settings.dedalus_log_retention_days,
    }
    return templates.TemplateResponse("admin/dedalus_activity.html", context)


@router.post("/admin/dedalus/logs/purge")
def admin_dedalus_logs_purge(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    settings = config.get_settings()
    removed = log_store.purge_older_than_days(settings.dedalus_log_retention_days)
    target = URL(request.url_for("admin_dedalus_logs")).include_query_params(
        message=f"Removed {removed} runs older than {settings.dedalus_log_retention_days} days",
        severity="success",
    )
    return RedirectResponse(str(target), status_code=303)


@router.get("/admin/dedalus/logs/export")
def admin_dedalus_logs_export(
    session_user: SessionUser = Depends(require_session_user),
    user_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    _require_admin(session_user)
    runs = log_store.fetch_runs(
        limit=limit,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "run_id",
            "created_at",
            "completed_at",
            "status",
            "user_id",
            "entity_type",
            "entity_id",
            "model",
            "prompt",
            "response",
            "error",
        ]
    )
    for run in runs:
        writer.writerow(
            [
                run.run_id,
                run.created_at,
                run.completed_at or "",
                run.status,
                run.user_id or "",
                run.entity_type or "",
                run.entity_id or "",
                run.model or "",
                (run.prompt or "").replace("\n", " "),
                (run.response or "").replace("\n", " "),
                (run.error or "").replace("\n", " "),
            ]
        )
    csv_data = buffer.getvalue()
    buffer.close()
    filename = "dedalus_logs.csv"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return PlainTextResponse(content=csv_data, headers=headers, media_type="text/csv")


@router.get("/admin/profiles")
def admin_profile_directory(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    page: int = Query(1, ge=1),
    q: Optional[str] = Query(None, alias="username"),
    contact: Optional[str] = None,
):
    _require_admin(session_user)
    viewer = session_user.user
    session = session_user.session

    filters = member_directory_service.MemberDirectoryFilters(
        username=q,
        contact=contact,
    )

    directory_page = member_directory_service.list_members(
        db,
        viewer=viewer,
        page=page,
        filters=filters,
        page_size=PAGE_SIZE,
    )
    users = directory_page.profiles

    def _page_url(target_page: int) -> str:
        url: URL = request.url.include_query_params(page=target_page)
        return str(url)

    pagination = {
        "has_prev": directory_page.page > 1,
        "has_next": directory_page.page < directory_page.total_pages,
        "prev_url": _page_url(directory_page.page - 1) if directory_page.page > 1 else None,
        "next_url": _page_url(directory_page.page + 1)
        if directory_page.page < directory_page.total_pages
        else None,
    }

    context = {
        "request": request,
        "user": viewer,
        "session": session,
        "session_role": describe_session_role(viewer, session),
        "session_username": viewer.username,
        "session_avatar_url": _get_account_avatar(db, viewer.id),
        "profiles": users,
        "profiles_total": directory_page.total_count,
        "page": directory_page.page,
        "total_pages": directory_page.total_pages,
        "page_size": directory_page.page_size,
        "username_query": directory_page.filters.username or "",
        "contact_query": directory_page.filters.contact or "",
        "pagination": pagination,
        "filters_active": bool(directory_page.filters.username or directory_page.filters.contact),
        "clear_filters_url": request.url.path,
        "current_url": str(request.url),
    }
    return templates.TemplateResponse("admin/profiles.html", context)


@router.get("/admin/profiles/{user_id}")
def admin_profile_detail(
    request: Request,
    user_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    viewer = session_user.user
    session = session_user.session

    profile = db.get(User, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    request_statement = (
        select(HelpRequest)
        .where(HelpRequest.created_by_user_id == profile.id)
        .order_by(HelpRequest.created_at.desc())
    )
    help_requests = db.exec(request_statement).all()

    invite_statement = (
        select(InviteToken)
        .where(InviteToken.created_by_user_id == profile.id)
        .order_by(InviteToken.created_at.desc())
    )
    invite_tokens = db.exec(invite_statement).all()

    invited_by_value = user_attribute_service.get_attribute(
        db,
        user_id=profile.id,
        key=user_attribute_service.INVITED_BY_USER_ID_KEY,
    )
    invited_by_user = None
    if invited_by_value:
        try:
            invited_by_user_id = int(invited_by_value)
        except ValueError:
            invited_by_user_id = None
        if invited_by_user_id:
            invited_by_user = db.get(User, invited_by_user_id)

    invite_token_value = user_attribute_service.get_attribute(
        db,
        user_id=profile.id,
        key=user_attribute_service.INVITE_TOKEN_USED_KEY,
    )

    highlight = user_profile_highlight_service.get(db, profile.id)
    flash_message = request.query_params.get("message")
    flash_severity = request.query_params.get("severity", "info")

    context = {
        "request": request,
        "user": viewer,
        "session": session,
        "session_role": describe_session_role(viewer, session),
        "session_username": viewer.username,
        "session_avatar_url": _get_account_avatar(db, viewer.id),
        "profile": profile,
        "profile_avatar_url": _get_account_avatar(db, profile.id),
        "help_requests": help_requests,
        "invite_tokens": invite_tokens,
        "directory_url": "/admin/profiles",
        "invited_by_user": invited_by_user,
        "invite_token_used": invite_token_value,
        "now_utc": datetime.utcnow(),
        "highlight": highlight,
        "flash_message": flash_message,
        "flash_severity": flash_severity,
    }
    return templates.TemplateResponse("admin/profile_detail.html", context)


@router.post("/admin/profiles/{user_id}/highlight")
def admin_profile_highlight_action(
    request: Request,
    user_id: int,
    db: SessionDep,
    action: str = Form(...),
    override_text: str = Form(""),
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    message = ""
    severity = "success"
    text_value = override_text.strip()

    if action == "override":
        if not text_value:
            message = "Provide text for the manual override."
            severity = "error"
        else:
            user_profile_highlight_service.set_manual_override(
                db,
                user_id=user_id,
                text=text_value,
            )
            db.commit()
            message = "Saved manual override; echos immediately in profile view."
    elif action == "clear_override":
        record = user_profile_highlight_service.clear_manual_override(db, user_id=user_id)
        if record is None:
            severity = "error"
            message = "No highlight to clear."
        else:
            db.commit()
            message = "Manual override cleared; run glaze to refresh copy."
    elif action == "mark_stale":
        user_profile_highlight_service.mark_stale(
            db,
            user_id=user_id,
            reason="admin-request",
        )
        db.commit()
        message = "Marked highlight stale; queue a glaze run to regenerate."
    else:
        severity = "error"
        message = "Unknown action."

    target = URL(request.url_for("admin_profile_detail", user_id=user_id)).include_query_params(
        message=message,
        severity=severity,
    )
    return RedirectResponse(str(target), status_code=303)


@router.get("/admin/dedalus")
async def admin_dedalus_settings(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    settings = config.get_settings()
    has_key = bool(settings.dedalus_api_key)
    message: Optional[str] = None
    status: Optional[str] = None
    verification_message: Optional[str] = None
    verification_ok: Optional[bool] = None
    if request.query_params.get("verify") == "1":
        if not has_key:
            message = "Store a Dedalus API key before verifying."
            status = "error"
        else:
            job = _queue_dedalus_job(
                DEDALUS_VERIFY_ACTION,
                session_user.user.username,
                message="Verification job queued",
            )
            api_key = settings.dedalus_api_key or ""
            asyncio.create_task(
                _run_dedalus_job(job.id, api_key=api_key, action=DEDALUS_VERIFY_ACTION)
            )
            message = "Verification job queued. Watch the realtime status below."
            status = "info"
    formatted_verified = (
        friendly_time(settings.dedalus_api_key_verified_at)
        if settings.dedalus_api_key_verified_at
        else None
    )
    job_statuses = _dedalus_job_statuses()
    context = {
        "request": request,
        "user": session_user.user,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "current_key": settings.dedalus_api_key,
        "has_key": has_key,
        "last_verified": formatted_verified,
        "last_verified_raw": settings.dedalus_api_key_verified_at,
        "message": message,
        "status": status,
        "verification_message": verification_message,
        "verification_ok": verification_ok,
        "dedalus_verify_job": job_statuses.get(DEDALUS_VERIFY_ACTION),
        "dedalus_save_job": job_statuses.get(DEDALUS_SAVE_ACTION),
    }
    return templates.TemplateResponse("admin/dedalus_settings.html", context)


@router.post("/admin/dedalus")
async def admin_dedalus_settings_submit(
    request: Request,
    dedalus_api_key: str = Form(""),
    clear_key: Optional[str] = Form(None),
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    trimmed = dedalus_api_key.strip()
    message: Optional[str] = None
    status: Optional[str] = None
    verification_message: Optional[str] = None
    verification_ok: Optional[bool] = None

    new_value: Optional[str]
    if clear_key:
        new_value = ""
    elif trimmed:
        new_value = trimmed
    else:
        new_value = None

    if new_value is None:
        message = "No changes submitted."
        status = "info"
    else:
        try:
            _write_env_value(DEDALUS_ENV_KEY, new_value)
            os.environ[DEDALUS_ENV_KEY] = new_value
            config.reset_settings_cache()
            if new_value:
                job = _queue_dedalus_job(
                    DEDALUS_SAVE_ACTION,
                    session_user.user.username,
                    message="Verifying saved API key",
                )
                asyncio.create_task(
                    _run_dedalus_job(job.id, api_key=new_value, action=DEDALUS_SAVE_ACTION)
                )
                message = "Dedalus API key saved. Verification job queued."
                status = "success"
            else:
                _write_env_value(DEDALUS_ENV_VERIFIED, None)
                os.environ.pop(DEDALUS_ENV_VERIFIED, None)
                config.reset_settings_cache()
                message = "Dedalus API key removed."
                status = "success"
        except OSError as exc:
            message = f"Unable to update .env file: {exc}"
            status = "error"

    settings = config.get_settings()
    has_key = bool(settings.dedalus_api_key)
    formatted_verified = (
        friendly_time(settings.dedalus_api_key_verified_at)
        if settings.dedalus_api_key_verified_at
        else None
    )
    job_statuses = _dedalus_job_statuses()
    context = {
        "request": request,
        "user": session_user.user,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "current_key": settings.dedalus_api_key,
        "has_key": has_key,
        "last_verified": formatted_verified,
        "last_verified_raw": settings.dedalus_api_key_verified_at,
        "message": message,
        "status": status,
        "verification_message": verification_message,
        "verification_ok": verification_ok,
        "dedalus_verify_job": job_statuses.get(DEDALUS_VERIFY_ACTION),
        "dedalus_save_job": job_statuses.get(DEDALUS_SAVE_ACTION),
    }
    status_code = 500 if status == "error" else 200
    return templates.TemplateResponse("admin/dedalus_settings.html", context, status_code=status_code)
@router.get("/admin/comment-insights")
def admin_comment_insights(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    runs = _format_runs(comment_llm_insights_service.list_recent_runs(limit=20))
    context = {
        "request": request,
        "runs": runs,
        "snapshot_label": None,
        "provider": None,
    }
    return templates.TemplateResponse("admin/comment_insights.html", context)


@router.get("/admin/comment-insights/runs")
def admin_comment_insights_runs(
    request: Request,
    db: SessionDep,
    snapshot_label: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    runs = _format_runs(
        comment_llm_insights_service.list_recent_runs(
            limit=limit, snapshot_label=snapshot_label, provider=provider
        )
    )
    context = {
        "request": request,
        "runs": runs,
        "snapshot_label": snapshot_label,
        "provider": provider,
    }
    return templates.TemplateResponse("admin/partials/comment_insights_runs.html", context)


@router.get("/admin/comment-insights/runs/{run_id}/analyses")
def admin_comment_insights_run_detail(
    request: Request,
    run_id: str,
    db: SessionDep,
    limit: int = Query(default=200, ge=1, le=500),
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    raw_analyses = comment_llm_insights_service.list_analyses_for_run(run_id, limit=limit)
    analyses = []
    for item in raw_analyses:
        page = request_comment_service.get_comment_page(
            db,
            help_request_id=item.help_request_id,
            comment_id=item.comment_id,
        )
        payload = item.to_dict()
        payload["page"] = page
        analyses.append(payload)
    context = {
        "request": request,
        "analyses": analyses,
        "run_id": run_id,
    }
    return templates.TemplateResponse("admin/partials/comment_insights_run_detail.html", context)


@router.get("/admin/comment-insights/runs/{run_id}/export")
def admin_comment_insights_run_export(
    run_id: str,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    analyses = comment_llm_insights_service.list_analyses_for_run(run_id)
    if not analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    def iter_rows():
        import csv
        from io import StringIO
        header = [
            "run_id",
            "snapshot_label",
            "provider",
            "model",
            "comment_id",
            "help_request_id",
            "summary",
            "resource_tags",
            "request_tags",
            "audience",
            "residency_stage",
            "location",
            "location_precision",
            "urgency",
            "sentiment",
            "tags",
            "notes",
            "recorded_at",
        ]
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for item in analyses:
            writer.writerow(
                [
                    item.run_id,
                    item.snapshot_label,
                    item.provider,
                    item.model,
                    item.comment_id,
                    item.help_request_id,
                    item.summary,
                    json.dumps(item.resource_tags),
                    json.dumps(item.request_tags),
                    item.audience,
                    item.residency_stage,
                    item.location,
                    item.location_precision,
                    item.urgency,
                    item.sentiment,
                    json.dumps(item.tags),
                    item.notes,
                    item.recorded_at,
                ]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    filename = f"comment-insights-{run_id}.csv"
    return StreamingResponse(
        iter_rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _format_runs(runs):
    formatted = []
    for run in runs:
        started_at = run.started_at
        friendly = started_at
        try:
            friendly = friendly_time(datetime.fromisoformat(started_at))
        except Exception:  # pragma: no cover - fallback for legacy strings
            pass
        formatted.append(
            {
                "run_id": run.run_id,
                "snapshot_label": run.snapshot_label,
                "provider": run.provider,
                "model": run.model,
                "started_at": started_at,
                "started_at_friendly": friendly,
                "completed_batches": run.completed_batches,
                "total_batches": run.total_batches,
            }
        )
    return formatted
