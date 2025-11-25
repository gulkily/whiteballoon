from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import HelpRequest, RequestComment, User


MAX_COMMENT_LENGTH = 2000
DEFAULT_COMMENTS_PER_PAGE = 20
RECENT_PROFILE_COMMENTS_LIMIT = 5


def list_comments(
    session: Session,
    help_request_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[tuple[RequestComment, User]], int]:
    """
    List comments for a help request with optional pagination.
    Returns (comments, total_count).
    """
    base_query = (
        select(RequestComment, User)
        .join(User, User.id == RequestComment.user_id)
        .where(RequestComment.help_request_id == help_request_id)
        .where(RequestComment.deleted_at.is_(None))
    )
    
    # Get total count
    count_query = select(func.count()).select_from(RequestComment).where(
        RequestComment.help_request_id == help_request_id
    ).where(RequestComment.deleted_at.is_(None))
    total_count = session.exec(count_query).one() or 0
    
    # Apply pagination and ordering
    query = base_query.order_by(RequestComment.created_at.asc())
    if limit is not None:
        query = query.offset(offset).limit(limit)
    
    rows = session.exec(query).all()
    return rows, total_count


def list_recent_comments_for_user(
    session: Session,
    user_id: int,
    *,
    limit: int | None = None,
) -> list[tuple[RequestComment, HelpRequest]]:
    """Return the newest comments authored by a user, joined with their requests."""
    page_limit = limit if limit is not None else RECENT_PROFILE_COMMENTS_LIMIT
    stmt = (
        select(RequestComment, HelpRequest)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .where(RequestComment.user_id == user_id)
        .where(RequestComment.deleted_at.is_(None))
        .order_by(RequestComment.created_at.desc())
    )
    if page_limit:
        stmt = stmt.limit(page_limit)
    return session.exec(stmt).all()


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


def serialize_comment(comment: RequestComment, user: User, *, display_name: str | None = None) -> dict[str, object]:
    created_at_iso = comment.created_at.isoformat() if comment.created_at else None
    return {
        "id": comment.id,
        "body": comment.body,
        "created_at": created_at_iso,
        "created_at_iso": created_at_iso,
        "user_id": user.id,
        "username": user.username,
        "display_name": display_name,
        "sync_scope": comment.sync_scope,
    }
