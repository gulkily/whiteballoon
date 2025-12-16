from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AuthRequestStatus,
    AuthenticationRequest,
    User,
    UserSession,
)

from . import user_attribute_service


PEER_AUTH_REVIEWER_ATTRIBUTE_KEY = "peer_auth_reviewer"
DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 100
_TRUTHY_VALUES = {"1", "true", "yes", "on", "approved", "enabled"}


@dataclass(slots=True)
class PeerAuthSessionSummary:
    auth_request_id: str
    session_id: str
    user_id: int
    username: str
    auth_request_created_at: Optional[datetime]
    auth_request_expires_at: Optional[datetime]
    session_created_at: Optional[datetime]
    session_last_seen_at: Optional[datetime]
    verification_code: str
    ip_address: Optional[str]
    device_info: Optional[str]
    status: AuthRequestStatus
    is_session_fully_authenticated: bool


def _normalize_page_limit(limit: Optional[int]) -> int:
    if limit is None or limit <= 0:
        return DEFAULT_PAGE_LIMIT
    return min(limit, MAX_PAGE_LIMIT)


def _build_base_statement():  # noqa: ANN202 - sqlmodel select builder
    return (
        select(AuthenticationRequest, UserSession, User)
        .join(UserSession, UserSession.auth_request_id == AuthenticationRequest.id)
        .join(User, User.id == AuthenticationRequest.user_id)
    )


def _row_to_summary(
    auth_request: AuthenticationRequest,
    session_record: UserSession,
    user: User,
) -> PeerAuthSessionSummary:
    return PeerAuthSessionSummary(
        auth_request_id=auth_request.id,
        session_id=session_record.id,
        user_id=user.id,
        username=user.username,
        auth_request_created_at=auth_request.created_at,
        auth_request_expires_at=auth_request.expires_at,
        session_created_at=session_record.created_at,
        session_last_seen_at=session_record.last_seen_at,
        verification_code=auth_request.verification_code,
        ip_address=auth_request.ip_address,
        device_info=auth_request.device_info,
        status=auth_request.status,
        is_session_fully_authenticated=session_record.is_fully_authenticated,
    )


def list_peer_auth_sessions(
    session: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    pending_only: bool = True,
) -> list[PeerAuthSessionSummary]:
    page_limit = _normalize_page_limit(limit)
    statement = _build_base_statement().order_by(AuthenticationRequest.created_at.asc())
    if pending_only:
        statement = statement.where(AuthenticationRequest.status == AuthRequestStatus.pending)
    statement = statement.where(UserSession.is_fully_authenticated.is_(False))
    if offset > 0:
        statement = statement.offset(offset)
    statement = statement.limit(page_limit)
    rows = session.exec(statement).all()
    summaries: list[PeerAuthSessionSummary] = []
    for auth_request, session_record, user in rows:
        summaries.append(_row_to_summary(auth_request, session_record, user))
    return summaries


def count_peer_auth_sessions(
    session: Session,
    *,
    pending_only: bool = True,
) -> int:
    statement = _build_base_statement()
    if pending_only:
        statement = statement.where(AuthenticationRequest.status == AuthRequestStatus.pending)
    statement = statement.where(UserSession.is_fully_authenticated.is_(False))
    rows = session.exec(statement).all()
    return len(rows)


def get_peer_auth_session(
    session: Session,
    *,
    auth_request_id: str,
) -> Optional[PeerAuthSessionSummary]:
    statement = _build_base_statement().where(AuthenticationRequest.id == auth_request_id)
    row = session.exec(statement).first()
    if not row:
        return None
    auth_request, session_record, user = row
    return _row_to_summary(auth_request, session_record, user)


def user_is_peer_auth_reviewer(session: Session, *, user: User) -> bool:
    if user.is_admin:
        return True
    flag = user_attribute_service.get_attribute(
        session,
        user_id=user.id,
        key=PEER_AUTH_REVIEWER_ATTRIBUTE_KEY,
    )
    if not flag:
        return False
    normalized = flag.strip().lower()
    return normalized in _TRUTHY_VALUES


def require_peer_auth_reviewer(session: Session, *, user: User) -> None:
    if user_is_peer_auth_reviewer(session, user=user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Peer authentication reviewer access required",
    )
