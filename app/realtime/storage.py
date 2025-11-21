from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

LOG_PATH = Path("data/realtime_jobs.jsonl")
_MAX_RECORDS = 500


def persist_snapshot(snapshot: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    if LOG_PATH.exists():
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    lines.append(json.dumps(snapshot, ensure_ascii=False))
    if len(lines) > _MAX_RECORDS:
        lines = lines[-_MAX_RECORDS:]
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_history(limit: Optional[int] = None) -> List[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    if limit:
        lines = lines[-limit:]
    snapshots: List[dict[str, Any]] = []
    for line in lines:
        try:
            snapshots.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return snapshots


def reset_history() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
