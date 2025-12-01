from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DB_PATH = Path("data/comment_llm_insights.db")
_SCHEMA_QUERIES: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS comment_llm_runs (
        run_id TEXT PRIMARY KEY,
        snapshot_label TEXT NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_batches INTEGER NOT NULL,
        total_batches INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS comment_llm_analyses (
        comment_id INTEGER PRIMARY KEY,
        run_id TEXT NOT NULL,
        help_request_id INTEGER NOT NULL,
        summary TEXT,
        resource_tags TEXT,
        request_tags TEXT,
        audience TEXT,
        residency_stage TEXT,
        location TEXT,
        location_precision TEXT,
        urgency TEXT,
        sentiment TEXT,
        tags TEXT,
        notes TEXT,
        recorded_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES comment_llm_runs(run_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_comment_llm_analyses_run_id
        ON comment_llm_analyses(run_id)
    """,
)


def _ensure_parent() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def open_connection() -> sqlite3.Connection:
    _ensure_parent()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    for query in _SCHEMA_QUERIES:
        conn.execute(query)
    conn.commit()


def init_db() -> None:
    with open_connection() as conn:
        _migrate(conn)


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    snapshot_label: str
    provider: str
    model: str
    started_at: str
    completed_batches: int
    total_batches: int


@dataclass(frozen=True)
class AnalysisRecord:
    comment_id: int
    run_id: str
    help_request_id: int
    recorded_at: str


def insert_run(conn: sqlite3.Connection, record: RunRecord) -> None:
    conn.execute(
        """
        INSERT INTO comment_llm_runs (
            run_id, snapshot_label, provider, model, started_at, completed_batches, total_batches
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            snapshot_label=excluded.snapshot_label,
            provider=excluded.provider,
            model=excluded.model,
            started_at=excluded.started_at,
            completed_batches=excluded.completed_batches,
            total_batches=excluded.total_batches
        """,
        (
            record.run_id,
            record.snapshot_label,
            record.provider,
            record.model,
            record.started_at,
            record.completed_batches,
            record.total_batches,
        ),
    )
    conn.commit()


def insert_analyses(conn: sqlite3.Connection, rows: Iterable[tuple]) -> None:
    conn.executemany(
        """
        INSERT INTO comment_llm_analyses (
            comment_id,
            run_id,
            help_request_id,
            summary,
            resource_tags,
            request_tags,
            audience,
            residency_stage,
            location,
            location_precision,
            urgency,
            sentiment,
            tags,
            notes,
            recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(comment_id) DO UPDATE SET
            run_id=excluded.run_id,
            help_request_id=excluded.help_request_id,
            summary=excluded.summary,
            resource_tags=excluded.resource_tags,
            request_tags=excluded.request_tags,
            audience=excluded.audience,
            residency_stage=excluded.residency_stage,
            location=excluded.location,
            location_precision=excluded.location_precision,
            urgency=excluded.urgency,
            sentiment=excluded.sentiment,
            tags=excluded.tags,
            notes=excluded.notes,
            recorded_at=excluded.recorded_at
        """,
        list(rows),
    )
    conn.commit()
