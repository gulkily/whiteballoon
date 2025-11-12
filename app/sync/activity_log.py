from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

LOG_PATH = Path("data/sync_activity.json")
_MAX_EVENTS = 200


def _ensure_log_path() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_event(
    *,
    peer: str,
    action: str,
    status: str,
    triggered_by: str | None = None,
    message: str | None = None,
) -> None:
    _ensure_log_path()
    events = _read_all()
    events.append(
        {
            "peer": peer,
            "action": action,
            "status": status,
            "triggered_by": triggered_by,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    events = events[-_MAX_EVENTS:]
    LOG_PATH.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_events(limit: int = 20) -> list[dict[str, Any]]:
    events = _read_all()
    return list(reversed(events))[:limit]


def _read_all() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return data


def reset() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()


__all__ = ["append_event", "read_events", "reset"]
