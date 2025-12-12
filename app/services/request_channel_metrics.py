from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import RequestComment


def load_comment_counts(
    session: Session,
    request_ids: list[int],
    *,
    newer_than: Optional[datetime] = None,
) -> tuple[dict[int, int], dict[int, int]]:
    if not request_ids:
        return {}, {}

    stmt = (
        select(RequestComment.help_request_id, func.count())
        .where(RequestComment.help_request_id.in_(request_ids))
        .where(RequestComment.deleted_at.is_(None))
        .group_by(RequestComment.help_request_id)
    )
    total_counts = {request_id: count for request_id, count in session.exec(stmt).all()}

    unread_counts: dict[int, int] = {}
    if newer_than:
        unread_stmt = (
            select(RequestComment.help_request_id, func.count())
            .where(RequestComment.help_request_id.in_(request_ids))
            .where(RequestComment.deleted_at.is_(None))
            .where(RequestComment.created_at > newer_than)
            .group_by(RequestComment.help_request_id)
        )
        unread_counts = {
            request_id: count for request_id, count in session.exec(unread_stmt).all()
        }

    return total_counts, unread_counts
