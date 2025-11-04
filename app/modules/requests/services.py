from __future__ import annotations

from datetime import datetime
from typing import List, Sequence

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import HelpRequest, User


def list_requests(session: Session, *, limit: int = 50) -> List[HelpRequest]:
    statement = (
        select(HelpRequest)
        .where(HelpRequest.status != "pending")
        .order_by(HelpRequest.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def create_request(
    session: Session,
    *,
    user: User,
    description: str,
    contact_email: str | None,
    status_value: str = "open",
) -> HelpRequest:
    summary = description.strip()
    if not summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Description required")

    normalized_title = summary.splitlines()[0][:200]

    help_request = HelpRequest(
        title=normalized_title or None,
        description=summary,
        contact_email=contact_email or user.contact_email,
        created_by_user_id=user.id,
        status=status_value,
    )
    session.add(help_request)
    session.commit()
    session.refresh(help_request)
    return help_request


def mark_completed(session: Session, *, request_id: int, user: User) -> HelpRequest:
    help_request = session.get(HelpRequest, request_id)
    if not help_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if help_request.created_by_user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to complete this request")

    now = datetime.utcnow()
    help_request.status = "completed"
    help_request.completed_at = now
    help_request.updated_at = now
    session.add(help_request)
    session.commit()
    session.refresh(help_request)
    return help_request



def list_pending_requests_for_user(session: Session, *, user_id: int) -> List[HelpRequest]:
    statement = (
        select(HelpRequest)
        .where(HelpRequest.created_by_user_id == user_id, HelpRequest.status == "pending")
        .order_by(HelpRequest.created_at.asc())
    )
    return list(session.exec(statement).all())


def promote_pending_requests(session: Session, *, user_id: int) -> None:
    pending_requests = list_pending_requests_for_user(session, user_id=user_id)
    if not pending_requests:
        return

    now = datetime.utcnow()
    for request in pending_requests:
        request.status = "open"
        request.updated_at = now
        session.add(request)

    session.commit()


def load_creator_usernames(session: Session, requests: Sequence[HelpRequest]) -> dict[int, str]:
    creator_ids = {request.created_by_user_id for request in requests if request.created_by_user_id}
    if not creator_ids:
        return {}

    statement = select(User.id, User.username).where(User.id.in_(creator_ids))
    rows = session.exec(statement).all()
    return {user_id: username for user_id, username in rows}


def get_request_by_id(session: Session, *, request_id: int) -> HelpRequest:
    help_request = session.get(HelpRequest, request_id)
    if not help_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return help_request
