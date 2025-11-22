"""SQLite-backed log store for Dedalus interactions."""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

ISO_TS_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

_STORAGE_DIR = Path(os.getenv("WB_STORAGE_DIR", "storage"))
_DB_PATH = Path(os.getenv("DEDALUS_LOG_DB", _STORAGE_DIR / "dedalus_logs.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dedalus_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    user_id TEXT,
    entity_type TEXT,
    entity_id TEXT,
    model TEXT,
    prompt TEXT,
    response TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    context_hash TEXT,
    structured_label TEXT,
    structured_tools TEXT
);

CREATE TABLE IF NOT EXISTS dedalus_tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT,
    output TEXT,
    status TEXT,
    FOREIGN KEY(run_id) REFERENCES dedalus_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_created_at ON dedalus_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_calls_run_id ON dedalus_tool_calls(run_id);
"""

_ALTERS = (
    "ALTER TABLE dedalus_runs ADD COLUMN structured_label TEXT",
    "ALTER TABLE dedalus_runs ADD COLUMN structured_tools TEXT",
)

_init_lock = threading.Lock()
_initialized = False


def _now() -> str:
    return datetime.utcnow().strftime(ISO_TS_FORMAT)


def _connect() -> sqlite3.Connection:
    _ensure_initialized()
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(_DB_PATH)
        try:
            conn.executescript(_SCHEMA)
            for statement in _ALTERS:
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError:
                    pass
        finally:
            conn.close()
        _initialized = True


def _generate_run_id() -> str:
    return secrets.token_hex(16)


@dataclass
class RunRecord:
    run_id: str
    created_at: str
    completed_at: Optional[str]
    user_id: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    model: Optional[str]
    prompt: Optional[str]
    response: Optional[str]
    status: str
    error: Optional[str]
    context_hash: Optional[str]
    structured_label: Optional[str]
    structured_tools: Optional[str]
    tool_calls: list[dict]


def log_run_start(
    *,
    user_id: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[str],
    model: Optional[str],
    prompt: str,
    context_hash: Optional[str] = None,
    run_id: Optional[str] = None,
) -> str:
    """Persist the start of a Dedalus interaction and return the correlation ID."""

    run_identifier = run_id or _generate_run_id()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO dedalus_runs (
                run_id, created_at, user_id, entity_type, entity_id, model, prompt, status, context_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                run_identifier,
                _now(),
                user_id,
                entity_type,
                entity_id,
                model,
                prompt,
                context_hash,
            ),
        )
    return run_identifier


def append_tool_call(
    *,
    run_id: str,
    tool_name: str,
    arguments: Optional[dict | str] = None,
    output: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    payload_args = arguments
    if isinstance(arguments, dict):
        payload_args = json.dumps(arguments, ensure_ascii=False)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO dedalus_tool_calls (run_id, created_at, tool_name, arguments, output, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                _now(),
                tool_name,
                payload_args,
                output,
                status,
            ),
        )


def finalize_run(
    *,
    run_id: str,
    response: Optional[str],
    status: str,
    error: Optional[str] = None,
    structured_label: Optional[str] = None,
    structured_tools: Optional[str] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE dedalus_runs
            SET completed_at = ?, response = ?, status = ?, error = ?, structured_label = ?, structured_tools = ?
            WHERE run_id = ?
            """,
            (
                _now(),
                response,
                status,
                error,
                structured_label,
                structured_tools,
                run_id,
            ),
        )


def fetch_runs(
    *,
    limit: int = 50,
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[RunRecord]:
    """Return recent runs with optional filters and attached tool calls."""

    clauses = []
    params: list[str] = []
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if entity_id:
        clauses.append("entity_id = ?")
        params.append(entity_id)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT * FROM dedalus_runs
        {where}
        ORDER BY datetime(created_at) DESC
        LIMIT ?
    """
    params.append(str(limit))
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
        run_ids = [row["run_id"] for row in rows]
        tool_map = _fetch_tool_calls(conn, run_ids)
    records: list[RunRecord] = []
    for row in rows:
        keys = row.keys()
        records.append(
            RunRecord(
                run_id=row["run_id"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                user_id=row["user_id"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                model=row["model"],
                prompt=row["prompt"],
                response=row["response"],
                status=row["status"],
                error=row["error"],
                context_hash=row["context_hash"],
                structured_label=row["structured_label"] if "structured_label" in keys else None,
                structured_tools=row["structured_tools"] if "structured_tools" in keys else None,
                tool_calls=tool_map.get(row["run_id"], []),
            )
        )
    return records


def _fetch_tool_calls(conn: sqlite3.Connection, run_ids: Iterable[str]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    if not run_ids:
        return result
    placeholders = ",".join("?" for _ in run_ids)
    query = f"""
        SELECT run_id, created_at, tool_name, arguments, output, status
        FROM dedalus_tool_calls
        WHERE run_id IN ({placeholders})
        ORDER BY datetime(created_at)
    """
    for row in conn.execute(query, list(run_ids)):
        result.setdefault(row["run_id"], []).append(
            {
                "created_at": row["created_at"],
                "tool_name": row["tool_name"],
                "arguments": row["arguments"],
                "output": row["output"],
                "status": row["status"],
            }
        )
    return result


def purge_older_than(cutoff_iso: str) -> int:
    """Delete runs (and cascading tool calls) older than the cutoff; returns rows removed."""

    with _connect() as conn:
        conn.execute(
            "DELETE FROM dedalus_tool_calls WHERE run_id IN (SELECT run_id FROM dedalus_runs WHERE completed_at < ?)",
            (cutoff_iso,),
        )
        cur = conn.execute("DELETE FROM dedalus_runs WHERE completed_at < ?", (cutoff_iso,))
        return cur.rowcount


def purge_older_than_days(days: int) -> int:
    cutoff = datetime.utcnow() - timedelta(days=max(0, days))
    iso = cutoff.strftime(ISO_TS_FORMAT)
    return purge_older_than(iso)
