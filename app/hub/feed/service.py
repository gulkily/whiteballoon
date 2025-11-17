from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy import func
from sqlmodel import select

from .db import init_feed_db, session_scope
from .models import HubFeedComment, HubFeedRequest
from .schema import HubFeedCommentDTO, HubFeedPageDTO, HubFeedRequestDTO

DEFAULT_FEED_PAGE_SIZE = 20
COMMENTS_PREVIEW_LIMIT = 3


def list_feed_requests(*, limit: int = DEFAULT_FEED_PAGE_SIZE, offset: int = 0) -> HubFeedPageDTO:
    init_feed_db()
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    with session_scope() as session:
        total = session.exec(select(func.count()).select_from(HubFeedRequest)).one()
        rows: Sequence[HubFeedRequest] = session.exec(
            select(HubFeedRequest)
            .order_by(HubFeedRequest.updated_at.desc(), HubFeedRequest.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()

        request_ids = [row.id for row in rows if row.id is not None]
        comment_map: dict[int, list[HubFeedComment]] = {}
        if request_ids:
            comment_rows: Sequence[HubFeedComment] = session.exec(
                select(HubFeedComment)
                .where(HubFeedComment.request_id.in_(request_ids))
                .order_by(HubFeedComment.created_at.asc())
            ).all()
            for comment in comment_rows:
                if comment.request_id is None:
                    continue
                comment_map.setdefault(comment.request_id, []).append(comment)

        items = [
            _to_request_dto(row, comment_map.get(row.id or 0, [])[:COMMENTS_PREVIEW_LIMIT]) for row in rows
        ]
    next_offset = offset + limit if offset + limit < total else None
    return HubFeedPageDTO(items=items, total=total, next_offset=next_offset)


def _to_request_dto(
    request: HubFeedRequest,
    comments: Iterable[HubFeedComment],
) -> HubFeedRequestDTO:
    return HubFeedRequestDTO(
        id=request.id or 0,
        peer_name=request.peer_name,
        manifest_digest=request.manifest_digest,
        source_request_id=request.source_request_id,
        source_instance=request.source_instance,
        title=request.title,
        description=request.description,
        status=request.status,
        sync_scope=request.sync_scope,
        contact_email=request.contact_email,
        created_by_id=request.created_by_id,
        created_by_username=request.created_by_username,
        updated_at=_ensure_datetime(request.updated_at),
        last_comment_at=request.last_comment_at,
        comment_count=request.comment_count,
        comments=[_to_comment_dto(comment) for comment in comments],
    )


def _to_comment_dto(comment: HubFeedComment) -> HubFeedCommentDTO:
    return HubFeedCommentDTO(
        id=comment.id or 0,
        request_id=comment.request_id or 0,
        username=comment.username,
        body=comment.body,
        created_at=_ensure_datetime(comment.created_at),
        source_instance=comment.source_instance,
    )


def _ensure_datetime(value: datetime | None) -> datetime:
    if value:
        return value
    return datetime.utcnow()
