from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Iterable

from app.models import User

PRESENCE_TTL = timedelta(seconds=20)
TYPING_TTL = timedelta(seconds=6)


@dataclass
class _PresenceEntry:
    user_id: int
    username: str
    request_id: int
    last_seen_at: datetime
    typing_until: datetime | None = None


_LOCK = Lock()
_ENTRIES: Dict[tuple[int, int], _PresenceEntry] = {}


def mark_presence(user: User, request_id: int, *, typing: bool = False) -> None:
    now = datetime.utcnow()
    key = (request_id, user.id)
    with _LOCK:
        entry = _ENTRIES.get(key)
        if not entry:
            entry = _PresenceEntry(
                user_id=user.id,
                username=user.username,
                request_id=request_id,
                last_seen_at=now,
            )
        entry.last_seen_at = now
        if typing:
            entry.typing_until = now + TYPING_TTL
        _ENTRIES[key] = entry
        _prune_locked(now)


def list_presence(request_ids: Iterable[int]) -> dict[int, dict[str, object]]:
    now = datetime.utcnow()
    with _LOCK:
        _prune_locked(now)
        result: dict[int, dict[str, object]] = {}
        request_scope = set(request_ids)
        for (request_id, _), entry in _ENTRIES.items():
            if request_scope and request_id not in request_scope:
                continue
            payload = result.setdefault(request_id, {"online": 0, "typing": []})
            payload["online"] += 1
            if entry.typing_until and entry.typing_until > now:
                payload["typing"].append(entry.username)
        return result


def _prune_locked(now: datetime) -> None:
    expired: list[tuple[int, int]] = []
    for key, entry in _ENTRIES.items():
        if now - entry.last_seen_at > PRESENCE_TTL:
            expired.append(key)
    for key in expired:
        _ENTRIES.pop(key, None)
