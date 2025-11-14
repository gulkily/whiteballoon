from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlmodel import select

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import User
from app.routes.ui.helpers import describe_session_role, templates
from app.services import user_attribute_service
from starlette.datastructures import URL

router = APIRouter(tags=["ui"])
PAGE_SIZE = 25


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
    }
    return templates.TemplateResponse("admin/profiles.html", context)
