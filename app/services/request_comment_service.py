from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlmodel import Session, select

from app.models import RequestComment, User


MAX_COMMENT_LENGTH = 2000


def list_comments(session: Session, help_request_id: int) -> list[tuple[RequestComment, User]]:
    rows = session.exec(
        select(RequestComment, User)
        .where(RequestComment.help_request_id == help_request_id)
        .where(RequestComment.deleted_at.is_(None))
        .where(RequestComment.user_id == User.id)
        .order_by(RequestComment.created_at.asc())
    ).all()
    return rows


def add_comment(
    session: Session,
    *,
    help_request_id: int,
    user_id: int,
    body: str,
) -> RequestComment:
    trimmed = body.strip()
    if not trimmed:
        raise ValueError("Comment cannot be empty")
    if len(trimmed) > MAX_COMMENT_LENGTH:
        raise ValueError("Comment exceeds maximum length")

    comment = RequestComment(
        help_request_id=help_request_id,
        user_id=user_id,
        body=trimmed,
        created_at=datetime.utcnow(),
    )
    session.add(comment)
    session.flush()
    session.refresh(comment)
    return comment


def soft_delete_comment(session: Session, comment_id: int) -> None:
    comment = session.get(RequestComment, comment_id)
    if not comment:
        return
    comment.deleted_at = datetime.utcnow()
    session.add(comment)
    session.flush()
