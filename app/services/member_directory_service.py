from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Optional

from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.models import User
from app.services import user_attribute_service

DEFAULT_PAGE_SIZE = 25


@dataclass(slots=True)
class MemberDirectoryFilters:
    username: Optional[str] = None
    contact: Optional[str] = None


@dataclass(slots=True)
class MemberDirectoryPage:
    profiles: list[User]
    total_count: int
    page: int
    total_pages: int
    page_size: int
    filters: MemberDirectoryFilters


def list_members(
    session: Session,
    *,
    viewer: User,
    page: int = 1,
    filters: Optional[MemberDirectoryFilters] = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> MemberDirectoryPage:
    page = max(page, 1)
    page_size = max(page_size, 1)

    normalized_filters = _normalize_filters(filters)

    base_statement = select(User)
    count_statement = select(func.count()).select_from(User)

    base_statement = _apply_filters(base_statement, normalized_filters)
    count_statement = _apply_filters(count_statement, normalized_filters)

    visibility_clause = _build_visibility_clause(session, viewer)
    if visibility_clause is not None:
        base_statement = base_statement.where(visibility_clause)
        count_statement = count_statement.where(visibility_clause)

    total_count_raw = session.exec(count_statement).one()
    total_count = _coerce_count(total_count_raw)

    total_pages = max(1, ceil(total_count / page_size)) if total_count else 1
    current_page = min(page, total_pages) if total_pages else 1
    offset = (current_page - 1) * page_size if total_count else 0

    profiles = (
        session.exec(
            base_statement.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        ).all()
        if total_count
        else []
    )

    return MemberDirectoryPage(
        profiles=profiles,
        total_count=total_count,
        page=current_page,
        total_pages=total_pages,
        page_size=page_size,
        filters=normalized_filters,
    )


def _normalize_filters(filters: Optional[MemberDirectoryFilters]) -> MemberDirectoryFilters:
    if not filters:
        return MemberDirectoryFilters()
    return MemberDirectoryFilters(
        username=_normalize_value(filters.username),
        contact=_normalize_value(filters.contact),
    )


def _normalize_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    return trimmed or None


def _apply_filters(statement, filters: MemberDirectoryFilters):
    if filters.username:
        lowered = filters.username.lower()
        statement = statement.where(func.lower(User.username).like(f"%{lowered}%"))
    if filters.contact:
        lowered = filters.contact.lower()
        statement = statement.where(func.lower(User.contact_email).like(f"%{lowered}%"))
    return statement


def _build_visibility_clause(session: Session, viewer: User):
    if viewer.is_admin:
        return None

    invitee_ids = user_attribute_service.list_invitee_user_ids(
        session,
        inviter_user_id=viewer.id,
    )
    allowed_ids = {user_id for user_id in invitee_ids if user_id is not None}
    if viewer.id is not None:
        allowed_ids.add(viewer.id)

    if not allowed_ids:
        return User.sync_scope == "public"

    return or_(
        User.sync_scope == "public",
        User.id.in_(list(allowed_ids)),
    )


def _coerce_count(value) -> int:
    if isinstance(value, tuple):
        raw_value = value[0]
    else:
        raw_value = value
    return int(raw_value or 0)
