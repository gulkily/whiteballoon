from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from app.services import comment_llm_insights_db

DEFAULT_SOURCE = Path("storage/comment_llm_runs/comment_analyses.jsonl")


def _rows_from_jsonl(path: Path) -> tuple[list[tuple], dict[str, dict]]:
    rows: list[tuple] = []
    runs: dict[str, dict] = {}
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            analysis = payload.get("analysis", {})
            run_id = payload.get("run_id", "unknown-run")
            runs.setdefault(
                run_id,
                {
                    "snapshot_label": payload.get("snapshot_label", "unknown"),
                    "provider": payload.get("provider", "unknown"),
                    "model": payload.get("model", "unknown"),
                    "started_at": payload.get("recorded_at", ""),
                },
            )
            rows.append(
                (
                    payload.get("comment_id"),
                    run_id,
                    payload.get("help_request_id"),
                    analysis.get("summary", ""),
                    json.dumps(analysis.get("resource_tags", [])),
                    json.dumps(analysis.get("request_tags", [])),
                    analysis.get("audience", ""),
                    analysis.get("residency_stage", ""),
                    analysis.get("location", ""),
                    analysis.get("location_precision", ""),
                    analysis.get("urgency", ""),
                    analysis.get("sentiment", ""),
                    json.dumps(analysis.get("tags", [])),
                    analysis.get("notes", ""),
                    payload.get("recorded_at", ""),
                )
            )
    return rows, runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.comment_llm_insights_backfill",
        description="Replay JSONL comment analyses into the SQLite insights DB.",
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to comment_analyses.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing")
    ns = parser.parse_args(argv)

    rows, runs = _rows_from_jsonl(ns.source)
    print(f"Loaded {len(rows)} analyses from {ns.source}")
    if ns.dry_run:
        print(f"Would insert/update {len(runs)} runs")
        return 0

    with comment_llm_insights_db.open_connection() as conn:
        for run_id, meta in runs.items():
            comment_llm_insights_db.insert_run(
                conn,
                comment_llm_insights_db.RunRecord(
                    run_id=run_id,
                    snapshot_label=meta.get("snapshot_label", "unknown"),
                    provider=meta.get("provider", "unknown"),
                    model=meta.get("model", "unknown"),
                    started_at=meta.get("started_at", ""),
                    completed_batches=0,
                    total_batches=0,
                ),
            )
        comment_llm_insights_db.insert_analyses(conn, rows)
    print("Backfill complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
