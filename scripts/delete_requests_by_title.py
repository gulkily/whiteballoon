#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, func, or_, select
from sqlmodel import Session

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import get_engine  # noqa: E402
from app.models import (  # noqa: E402
    CommentAttribute,
    CommentPromotion,
    HelpRequest,
    RecurringRequestRun,
    RequestAttribute,
    RequestComment,
)

CHAT_CACHE_DIR = REPO_ROOT / "storage" / "cache" / "request_chats"
CHAT_EMBED_CACHE_DIR = REPO_ROOT / "storage" / "cache" / "request_chat_embeddings"


def _count_rows(session: Session, statement) -> int:
    return int(session.exec(statement).one()[0])


def _delete_comment_attributes(session: Session, comment_ids: list[int]) -> int:
    if not comment_ids:
        return 0
    stmt = delete(CommentAttribute).where(CommentAttribute.comment_id.in_(comment_ids))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _delete_comment_promotions(session: Session, request_ids: list[int], comment_ids: list[int]) -> int:
    conditions = []
    if request_ids:
        conditions.append(CommentPromotion.request_id.in_(request_ids))
    if comment_ids:
        conditions.append(CommentPromotion.comment_id.in_(comment_ids))
    if not conditions:
        return 0
    stmt = delete(CommentPromotion).where(or_(*conditions))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _delete_request_comments(session: Session, comment_ids: list[int]) -> int:
    if not comment_ids:
        return 0
    stmt = delete(RequestComment).where(RequestComment.id.in_(comment_ids))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _delete_request_attributes(session: Session, request_ids: list[int]) -> int:
    if not request_ids:
        return 0
    stmt = delete(RequestAttribute).where(RequestAttribute.request_id.in_(request_ids))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _delete_recurring_runs(session: Session, request_ids: list[int]) -> int:
    if not request_ids:
        return 0
    stmt = delete(RecurringRequestRun).where(RecurringRequestRun.request_id.in_(request_ids))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _delete_requests(session: Session, request_ids: list[int]) -> int:
    if not request_ids:
        return 0
    stmt = delete(HelpRequest).where(HelpRequest.id.in_(request_ids))
    result = session.exec(stmt)
    return int(result.rowcount or 0)


def _remove_cache_files(request_ids: Iterable[int]) -> dict[str, int]:
    deleted_counts = {"chat_index": 0, "chat_embeddings": 0}
    for request_id in request_ids:
        chat_cache = CHAT_CACHE_DIR / f"request_{request_id}.json"
        if chat_cache.exists():
            chat_cache.unlink()
            deleted_counts["chat_index"] += 1
        embed_cache = CHAT_EMBED_CACHE_DIR / f"request_{request_id}.json"
        if embed_cache.exists():
            embed_cache.unlink()
            deleted_counts["chat_embeddings"] += 1
    return deleted_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete help requests by exact title.")
    parser.add_argument("title", help="Exact title to match.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes.",
    )
    args = parser.parse_args()

    with Session(get_engine()) as session:
        request_ids = session.exec(
            select(HelpRequest.id).where(HelpRequest.title == args.title)
        ).scalars().all()
        if not request_ids:
            print(f'No requests found with title "{args.title}".')
            return

        print(f'Found {len(request_ids)} request(s) matching "{args.title}": {request_ids}')

        comment_ids: list[int] = []
        comment_attr_count = 0
        promotion_count = 0
        comment_count = 0
        attribute_count = 0
        run_count = 0

        stmt = select(RequestComment.id).where(RequestComment.help_request_id.in_(request_ids))
        comment_ids = session.exec(stmt).scalars().all()
        comment_count = len(comment_ids)

        if comment_ids:
            comment_attr_count = _count_rows(
                session,
                select(func.count())
                .select_from(CommentAttribute)
                .where(CommentAttribute.comment_id.in_(comment_ids)),
            )
        if request_ids or comment_ids:
            clauses = []
            if request_ids:
                clauses.append(CommentPromotion.request_id.in_(request_ids))
            if comment_ids:
                clauses.append(CommentPromotion.comment_id.in_(comment_ids))
            if clauses:
                promotion_count = _count_rows(
                    session,
                    select(func.count())
                    .select_from(CommentPromotion)
                    .where(or_(*clauses)),
                )

        if request_ids:
            attribute_count = _count_rows(
                session,
                select(func.count())
                .select_from(RequestAttribute)
                .where(RequestAttribute.request_id.in_(request_ids)),
            )
            run_count = _count_rows(
                session,
                select(func.count())
                .select_from(RecurringRequestRun)
                .where(RecurringRequestRun.request_id.in_(request_ids)),
            )

        print("Pending deletions:")
        print(f"  Help requests      : {len(request_ids)}")
        print(f"  Request comments   : {comment_count}")
        print(f"  Comment attributes : {comment_attr_count}")
        print(f"  Comment promotions : {promotion_count}")
        print(f"  Request attributes : {attribute_count}")
        print(f"  Recurring runs     : {run_count}")

        if args.dry_run:
            print("Dry run complete. No changes applied.")
            return

        deleted_attr = _delete_request_attributes(session, request_ids)
        deleted_runs = _delete_recurring_runs(session, request_ids)
        deleted_comment_attrs = _delete_comment_attributes(session, comment_ids)
        deleted_promotions = _delete_comment_promotions(session, request_ids, comment_ids)
        deleted_comments = _delete_request_comments(session, comment_ids)
        deleted_requests = _delete_requests(session, request_ids)
        session.commit()

        cache_stats = _remove_cache_files(request_ids)

        print("Deletion results:")
        print(f"  Help requests deleted      : {deleted_requests}")
        print(f"  Request comments deleted   : {deleted_comments}")
        print(f"  Comment attributes deleted : {deleted_comment_attrs}")
        print(f"  Comment promotions deleted : {deleted_promotions}")
        print(f"  Request attributes deleted : {deleted_attr}")
        print(f"  Recurring runs deleted     : {deleted_runs}")
        print(
            f"  Chat index cache removed   : {cache_stats['chat_index']} file(s)"
        )
        print(
            f"  Chat embedding cache removed: {cache_stats['chat_embeddings']} file(s)"
        )


if __name__ == "__main__":
    main()
