from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

from sqlmodel import select

from .db import init_feed_db, session_scope
from .models import HubFeedComment, HubFeedManifest, HubFeedRequest
from .parser import (
    ParsedComment,
    ParsedRequest,
    ParsedUser,
    iter_request_files,
    iter_user_files,
    parse_request_file,
    parse_user_file,
)

logger = logging.getLogger("whiteballoon.hub.feed")


def ingest_bundle(
    bundle_root: Path,
    *,
    peer_name: str,
    manifest_digest: str,
    signed_at: datetime,
) -> None:
    """Parse bundle contents into the structured feed store."""

    init_feed_db()
    user_lookup = _build_user_lookup(bundle_root)
    now = datetime.now(timezone.utc)
    seen_request_keys: set[Tuple[str, int]] = set()
    newest_updated_at: datetime | None = None

    with session_scope() as session:
        manifest = session.exec(
            select(HubFeedManifest).where(HubFeedManifest.manifest_digest == manifest_digest)
        ).first()
        if not manifest:
            manifest = HubFeedManifest(
                peer_name=peer_name,
                manifest_digest=manifest_digest,
                signed_at=signed_at,
                bundle_updated_at=None,
            )
        else:
            manifest.peer_name = peer_name
            manifest.signed_at = signed_at
        manifest.ingested_at = now
        session.add(manifest)

        for request_path in iter_request_files(bundle_root):
            try:
                parsed = parse_request_file(request_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to parse %s: %s", request_path, exc)
                continue
            if parsed.sync_scope != "public":
                continue
            if not parsed.source_request_id or not parsed.instance:
                continue

            key = (parsed.instance, parsed.source_request_id)
            seen_request_keys.add(key)

            db_request = session.exec(
                select(HubFeedRequest)
                .where(HubFeedRequest.source_instance == parsed.instance)
                .where(HubFeedRequest.source_request_id == parsed.source_request_id)
            ).first()
            if not db_request:
                db_request = HubFeedRequest(
                    peer_name=peer_name,
                    manifest_digest=manifest_digest,
                    source_request_id=parsed.source_request_id,
                    source_instance=parsed.instance,
                    title=parsed.title,
                    description=parsed.description,
                    status=parsed.status,
                    sync_scope=parsed.sync_scope,
                    contact_email=parsed.contact_email,
                    created_by_id=parsed.created_by_id,
                    created_by_username=parsed.created_by_username or user_lookup.get(parsed.created_by_id),
                    updated_at=parsed.updated_at or now,
                )
            else:
                db_request.peer_name = peer_name
                db_request.manifest_digest = manifest_digest
                db_request.title = parsed.title
                db_request.description = parsed.description
                db_request.status = parsed.status
                db_request.sync_scope = parsed.sync_scope
                db_request.contact_email = parsed.contact_email
                db_request.created_by_id = parsed.created_by_id
                db_request.created_by_username = parsed.created_by_username or user_lookup.get(parsed.created_by_id)
                db_request.updated_at = parsed.updated_at or db_request.updated_at

            db_request.ingested_at = now
            session.add(db_request)
            session.flush()

            public_comments = [c for c in parsed.comments if c.sync_scope == "public"]
            _sync_comments(
                session,
                db_request,
                public_comments,
                manifest_digest,
                now,
            )

            if public_comments:
                last_comment_at = max((c.created_at or db_request.updated_at or now) for c in public_comments)
            else:
                last_comment_at = None
            db_request.comment_count = len(public_comments)
            db_request.last_comment_at = last_comment_at

            if parsed.updated_at and (not newest_updated_at or parsed.updated_at > newest_updated_at):
                newest_updated_at = parsed.updated_at

        _purge_missing_requests(session, peer_name, seen_request_keys)

        manifest.bundle_updated_at = newest_updated_at or now
        session.add(manifest)


def _build_user_lookup(bundle_root: Path) -> Dict[int, str]:
    lookup: Dict[int, str] = {}
    for user_path in iter_user_files(bundle_root):
        try:
            parsed = parse_user_file(user_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to parse %s: %s", user_path, exc)
            continue
        if parsed.sync_scope != "public":
            continue
        if parsed.user_id is None or not parsed.username:
            continue
        lookup[parsed.user_id] = parsed.username
    return lookup


def _sync_comments(
    session,
    db_request: HubFeedRequest,
    comments: Iterable[ParsedComment],
    manifest_digest: str,
    now: datetime,
) -> None:
    existing = session.exec(
        select(HubFeedComment)
        .where(HubFeedComment.source_instance == db_request.source_instance)
        .where(HubFeedComment.source_request_id == db_request.source_request_id)
    ).all()
    existing_map: dict[tuple[int, str], HubFeedComment] = {}
    for db_comment in existing:
        if db_comment.source_comment_id is None:
            continue
        existing_map[(db_comment.source_comment_id, db_comment.source_instance)] = db_comment
    seen_keys: set[tuple[int | None, str]] = set()

    for comment in comments:
        if comment.source_comment_id is None:
            continue
        key = (comment.source_comment_id, db_request.source_instance)
        seen_keys.add(key)
        db_comment = existing_map.get(key)
        created_at = comment.created_at or db_request.updated_at or now
        if not db_comment:
            db_comment = HubFeedComment(
                request_id=db_request.id,
                peer_name=db_request.peer_name,
                manifest_digest=manifest_digest,
                source_instance=db_request.source_instance,
                source_request_id=db_request.source_request_id,
                source_comment_id=comment.source_comment_id,
                username=comment.username,
                body=comment.body,
                sync_scope=comment.sync_scope,
                created_at=created_at,
            )
        else:
            db_comment.request_id = db_request.id
            db_comment.peer_name = db_request.peer_name
            db_comment.manifest_digest = manifest_digest
            db_comment.username = comment.username
            db_comment.body = comment.body
            db_comment.sync_scope = comment.sync_scope
            db_comment.created_at = created_at
        session.add(db_comment)

    for db_comment in existing:
        key = (db_comment.source_comment_id, db_comment.source_instance)
        if key not in seen_keys:
            session.delete(db_comment)


def _purge_missing_requests(session, peer_name: str, seen_keys: set[tuple[str, int]]) -> None:
    rows = session.exec(select(HubFeedRequest).where(HubFeedRequest.peer_name == peer_name)).all()
    for row in rows:
        key = (row.source_instance, row.source_request_id)
        if key in seen_keys:
            continue
        comments = session.exec(
            select(HubFeedComment).where(HubFeedComment.request_id == row.id)
        ).all()
        for comment in comments:
            session.delete(comment)
        session.delete(row)
