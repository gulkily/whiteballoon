from __future__ import annotations

from datetime import datetime
import os
from math import ceil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from sqlalchemy import func
from sqlmodel import select

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import HelpRequest, InviteToken, User
from app import config
from app.routes.ui.helpers import friendly_time

try:
    from dedalus_labs import AsyncDedalus, DedalusRunner
except ImportError:  # pragma: no cover - optional dependency
    AsyncDedalus = None  # type: ignore
    DedalusRunner = None  # type: ignore
from app.routes.ui.helpers import describe_session_role, templates
from app.services import user_attribute_service
from starlette.datastructures import URL

router = APIRouter(tags=["ui"])
PAGE_SIZE = 25
ENV_PATH = Path(".env")
ENV_EXAMPLE_PATH = Path(".env.example")
DEDALUS_ENV_KEY = "DEDALUS_API_KEY"
DEDALUS_ENV_VERIFIED = "DEDALUS_API_KEY_VERIFIED_AT"


def _require_admin(session_user: SessionUser) -> None:
    if not session_user.user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_account_avatar(db: SessionDep, user_id: int) -> Optional[str]:
    return user_attribute_service.get_attribute(
        db,
        user_id=user_id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )


def _normalize_filter(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    return trimmed or None


def _apply_filters(statement, username_query: Optional[str], contact_query: Optional[str]):
    if username_query:
        lowered = username_query.lower()
        statement = statement.where(func.lower(User.username).like(f"%{lowered}%"))
    if contact_query:
        lowered = contact_query.lower()
        statement = statement.where(func.lower(User.contact_email).like(f"%{lowered}%"))
    return statement


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
    try:
        response = await runner.run(
            input="WhiteBalloon connectivity check",
            model="openai/gpt-5-mini",
        )
    except Exception as exc:  # pragma: no cover - external dependency
        return False, str(exc)
    summary = getattr(response, "final_output", None)
    if not summary and hasattr(response, "outputs"):
        summary = str(response.outputs)
    return True, summary or "Verified successfully."


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

    username_query = _normalize_filter(q)
    contact_query = _normalize_filter(contact)

    base_statement = select(User)
    count_statement = select(func.count()).select_from(User)
    base_statement = _apply_filters(base_statement, username_query, contact_query)
    count_statement = _apply_filters(count_statement, username_query, contact_query)

    total_count_raw = db.exec(count_statement).one()
    total_count = total_count_raw[0] if isinstance(total_count_raw, tuple) else total_count_raw
    total_count = total_count or 0

    total_pages = max(1, ceil(total_count / PAGE_SIZE)) if total_count else 1
    current_page = min(page, total_pages) if total_pages else 1
    offset = (current_page - 1) * PAGE_SIZE if total_count else 0

    users = (
        db.exec(
            base_statement.order_by(User.created_at.desc()).offset(offset).limit(PAGE_SIZE)
        ).all()
        if total_count
        else []
    )

    def _page_url(target_page: int) -> str:
        url: URL = request.url.include_query_params(page=target_page)
        return str(url)

    pagination = {
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_url": _page_url(current_page - 1) if current_page > 1 else None,
        "next_url": _page_url(current_page + 1) if current_page < total_pages else None,
    }

    context = {
        "request": request,
        "user": viewer,
        "session": session,
        "session_role": describe_session_role(viewer, session),
        "session_username": viewer.username,
        "session_avatar_url": _get_account_avatar(db, viewer.id),
        "profiles": users,
        "profiles_total": total_count,
        "page": current_page,
        "total_pages": total_pages,
        "page_size": PAGE_SIZE,
        "username_query": username_query or "",
        "contact_query": contact_query or "",
        "pagination": pagination,
        "filters_active": bool(username_query or contact_query),
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
    }
    return templates.TemplateResponse("admin/profile_detail.html", context)


@router.get("/admin/dedalus")
async def admin_dedalus_settings(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    _require_admin(session_user)
    settings = config.get_settings()
    has_key = bool(settings.dedalus_api_key)
    verification_message: Optional[str] = None
    verification_ok: Optional[bool] = None
    if has_key and request.query_params.get("verify") == "1":
        verification_ok, verification_message = await _verify_dedalus_api_key(settings.dedalus_api_key)
        if verification_ok:
            timestamp = datetime.utcnow().isoformat()
            _write_env_value(DEDALUS_ENV_VERIFIED, timestamp)
            os.environ[DEDALUS_ENV_VERIFIED] = timestamp
            config.reset_settings_cache()
            settings = config.get_settings()
    formatted_verified = (
        friendly_time(settings.dedalus_api_key_verified_at)
        if settings.dedalus_api_key_verified_at
        else None
    )
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
        "message": None,
        "status": None,
        "verification_message": verification_message,
        "verification_ok": verification_ok,
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
                verification_ok, verification_message = await _verify_dedalus_api_key(new_value)
                if verification_ok:
                    timestamp = datetime.utcnow().isoformat()
                    _write_env_value(DEDALUS_ENV_VERIFIED, timestamp)
                    os.environ[DEDALUS_ENV_VERIFIED] = timestamp
                    config.reset_settings_cache()
                    message = "Dedalus API key updated and verified."
                    status = "success"
                else:
                    _write_env_value(DEDALUS_ENV_VERIFIED, None)
                    os.environ.pop(DEDALUS_ENV_VERIFIED, None)
                    config.reset_settings_cache()
                    message = "Dedalus API key saved, but verification failed."
                    status = "error"
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
    }
    status_code = 500 if status == "error" else 200
    return templates.TemplateResponse("admin/dedalus_settings.html", context, status_code=status_code)
