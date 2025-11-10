from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlmodel import Session

from app.models import InviteMapCache
from app.services import invite_graph_service

CACHE_VERSION = "v1"
CACHE_TTL_SECONDS = 600  # 10 minutes


def get_cached_map(
    session: Session,
    *,
    user_id: int,
    now: Optional[datetime] = None,
) -> Optional[invite_graph_service.InviteMapPayload]:
    record = session.get(InviteMapCache, user_id)
    if not record:
        return None
    if record.version != CACHE_VERSION:
        return None

    now = now or datetime.utcnow()
    if now - record.generated_at > timedelta(seconds=CACHE_TTL_SECONDS):
        return None

    try:
        payload = json.loads(record.payload)
    except json.JSONDecodeError:
        return None

    return invite_graph_service.deserialize_invite_map(payload)


def store_cached_map(
    session: Session,
    *,
    user_id: int,
    invite_map: invite_graph_service.InviteMapPayload,
    version: str = CACHE_VERSION,
    generated_at: Optional[datetime] = None,
) -> InviteMapCache:
    data = invite_graph_service.serialize_invite_map(invite_map)
    serialized = json.dumps(data, separators=(",", ":"))
    now = generated_at or datetime.utcnow()

    record = session.get(InviteMapCache, user_id)
    if record:
        record.payload = serialized
        record.generated_at = now
        record.version = version
    else:
        record = InviteMapCache(
            user_id=user_id,
            payload=serialized,
            generated_at=now,
            version=version,
        )
        session.add(record)

    session.flush()
    return record


def invalidate_cache(session: Session, *, user_id: int) -> None:
    record = session.get(InviteMapCache, user_id)
    if record:
        session.delete(record)
        session.flush()


def invalidate_many(session: Session, user_ids: Iterable[int]) -> None:
    for user_id in set(user_ids):
        invalidate_cache(session, user_id=user_id)
