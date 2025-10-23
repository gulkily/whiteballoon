from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import HelpRequest, User


def list_requests(session: Session, *, limit: int = 50) -> List[HelpRequest]:
    statement = (
        select(HelpRequest)
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
