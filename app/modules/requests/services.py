from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import (
    HELP_REQUEST_STATUS_DRAFT,
    HELP_REQUEST_STATUS_OPEN,
    HELP_REQUEST_STATUS_PENDING,
    HelpRequest,
    RequestAttribute,
    User,
)
from app.services import request_pin_service


def list_requests(
    session: Session,
    *,
    limit: int | None = 50,
    search: str | None = None,
    statuses: Iterable[str] | None = None,
    pinned_only: bool = False,
    include_pending: bool = False,
) -> List[HelpRequest]:
    statement = select(HelpRequest).where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
    if pinned_only:
        statement = statement.join(
            RequestAttribute,
            (RequestAttribute.request_id == HelpRequest.id)
            & (RequestAttribute.key == request_pin_service.PIN_ATTRIBUTE_KEY),
        )
    if not include_pending:
        statement = statement.where(HelpRequest.status != "pending")
    if statuses:
        normalized = {status.strip().lower() for status in statuses if status}
        if normalized:
            statement = statement.where(HelpRequest.status.in_(normalized))
    if search:
        query = search.strip()
        if query:
            pattern = f"%{query.lower()}%"
            statement = statement.where(
                func.lower(HelpRequest.description).like(pattern)
                | func.lower(HelpRequest.title).like(pattern)
            )

    statement = statement.order_by(HelpRequest.created_at.desc())
    if limit is not None:
        statement = statement.limit(limit)
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

    help_request = HelpRequest(
        title=_derive_title(summary),
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


def get_request_by_id(
    session: Session,
    *,
    request_id: int,
    allow_draft_for_user_id: int | None = None,
) -> HelpRequest:
    help_request = session.get(HelpRequest, request_id)
    if not help_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if help_request.status == HELP_REQUEST_STATUS_DRAFT:
        if allow_draft_for_user_id and help_request.created_by_user_id == allow_draft_for_user_id:
            return help_request
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return help_request


def list_drafts_for_user(session: Session, *, user_id: int) -> List[HelpRequest]:
    statement = (
        select(HelpRequest)
        .where(HelpRequest.created_by_user_id == user_id)
        .where(HelpRequest.status == HELP_REQUEST_STATUS_DRAFT)
        .order_by(HelpRequest.updated_at.desc())
    )
    return list(session.exec(statement).all())


def save_draft(
    session: Session,
    *,
    user: User,
    description: str | None,
    contact_email: str | None,
    draft_id: int | None = None,
) -> HelpRequest:
    summary = _normalize_summary(description)
    normalized_title = _derive_title(summary)
    normalized_contact = contact_email or user.contact_email
    now = datetime.utcnow()

    if draft_id:
        help_request = _get_owned_draft(session, draft_id, user)
        help_request.description = summary
        help_request.title = normalized_title
        help_request.contact_email = normalized_contact
        help_request.updated_at = now
        session.add(help_request)
    else:
        help_request = HelpRequest(
            title=normalized_title,
            description=summary,
            contact_email=normalized_contact,
            created_by_user_id=user.id,
            status=HELP_REQUEST_STATUS_DRAFT,
        )
        session.add(help_request)

    session.commit()
    session.refresh(help_request)
    return help_request


def publish_draft(
    session: Session,
    *,
    draft_id: int,
    user: User,
    is_fully_authenticated: bool,
    description: str | None = None,
    contact_email: str | None = None,
) -> HelpRequest:
    help_request = _get_owned_draft(session, draft_id, user)
    new_summary = description if description is not None else help_request.description
    summary = _normalize_summary(new_summary)
    if not summary:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Description required to publish")

    help_request.description = summary
    help_request.title = _derive_title(summary)
    if contact_email is not None:
        help_request.contact_email = contact_email or user.contact_email
    elif not help_request.contact_email:
        help_request.contact_email = user.contact_email
    help_request.status = HELP_REQUEST_STATUS_OPEN if is_fully_authenticated else HELP_REQUEST_STATUS_PENDING
    help_request.completed_at = None
    help_request.updated_at = datetime.utcnow()
    session.add(help_request)
    session.commit()
    session.refresh(help_request)
    return help_request


def delete_draft(session: Session, *, draft_id: int, user: User) -> None:
    help_request = _get_owned_draft(session, draft_id, user)
    session.delete(help_request)
    session.commit()


def _get_owned_draft(session: Session, draft_id: int, user: User) -> HelpRequest:
    help_request = session.get(HelpRequest, draft_id)
    if not help_request or help_request.status != HELP_REQUEST_STATUS_DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    if help_request.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return help_request


def _normalize_summary(value: str | None) -> str:
    return (value or "").strip()


def _derive_title(summary: str) -> str | None:
    if not summary:
        return None
    first_line = summary.splitlines()[0] if summary else ""
    first_line = first_line.strip()
    if not first_line:
        return None
    return first_line[:200]
