from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, Sequence

STORE_DIR = Path("storage/comment_llm_runs")
ANALYSES_PATH = STORE_DIR / "comment_analyses.jsonl"
INDEX_PATH = STORE_DIR / "comment_index.json"


class AnalysisRecord(Protocol):
    comment_id: int
    help_request_id: int

    def to_dict(self) -> dict[str, object]:
        ...


@dataclass
class SaveStats:
    written: int
    skipped: int


def _ensure_dir() -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict[str, dict[str, str]]:
    if not INDEX_PATH.exists():
        return {}
    try:
        data = json.loads(INDEX_PATH.read_text())
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    normalized: dict[str, dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        normalized[key] = {str(k): str(v) for k, v in value.items() if isinstance(k, str)}
    return normalized


def _write_index(index: dict[str, dict[str, str]]) -> None:
    _ensure_dir()
    INDEX_PATH.write_text(json.dumps(index, indent=2))


def recorded_comment_ids() -> set[int]:
    index = _load_index()
    comment_ids: set[int] = set()
    for key in index:
        try:
            comment_ids.add(int(key))
        except ValueError:
            continue
    return comment_ids


def save_comment_analyses(
    *,
    analyses: Sequence[AnalysisRecord],
    snapshot_label: str,
    provider: str,
    model: str,
    run_id: str,
    batch_index: int,
    overwrite: bool,
) -> SaveStats:
    if not analyses:
        return SaveStats(written=0, skipped=0)
    _ensure_dir()
    index = _load_index()
    written_lines: list[str] = []
    written = 0
    skipped = 0
    for analysis in analyses:
        key = str(analysis.comment_id)
        if not overwrite and key in index:
            skipped += 1
            continue
        entry = {
            "comment_id": analysis.comment_id,
            "help_request_id": analysis.help_request_id,
            "snapshot_label": snapshot_label,
            "provider": provider,
            "model": model,
            "run_id": run_id,
            "batch_index": batch_index,
            "recorded_at": datetime.utcnow().isoformat(),
            "analysis": analysis.to_dict(),
        }
        written_lines.append(json.dumps(entry))
        index[key] = {
            "run_id": run_id,
            "batch_index": str(batch_index),
            "recorded_at": entry["recorded_at"],
        }
        written += 1
    if written_lines:
        with ANALYSES_PATH.open("a", encoding="utf-8") as handle:
            for line in written_lines:
                handle.write(line + "\n")
        _write_index(index)
    return SaveStats(written=written, skipped=skipped)
