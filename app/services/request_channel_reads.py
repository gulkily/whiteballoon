from __future__ import annotations

from threading import Lock
from typing import Dict, Iterable

_LOCK = Lock()
_READ_COUNTS: Dict[tuple[str, int], int] = {}


def mark_read(session_id: str, request_id: int, *, comment_count: int) -> None:
    key = (session_id, request_id)
    with _LOCK:
        _READ_COUNTS[key] = max(0, comment_count)


def get_read_counts(session_id: str, request_ids: Iterable[int]) -> dict[int, int]:
    scope = set(request_ids)
    with _LOCK:
        result: dict[int, int] = {}
        for (record_session_id, request_id), count in _READ_COUNTS.items():
            if record_session_id != session_id:
                continue
            if scope and request_id not in scope:
                continue
            result[request_id] = count
        return result
