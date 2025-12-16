from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Iterable, Optional

LEDGER_PATH = Path("storage/peer_auth_ledger.db")

_SCHEMA_QUERIES: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_request_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        requester_user_id INTEGER NOT NULL,
        reviewer_user_id INTEGER NOT NULL,
        decision TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL,
        checksum TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_decisions_auth_request
        ON decisions(auth_request_id)
    """,
)

_lock = Lock()


@dataclass(frozen=True)
class LedgerEntry:
    auth_request_id: str
    session_id: str
    requester_user_id: int
    reviewer_user_id: int
    decision: str
    note: str
    created_at: datetime
    checksum: str


def _ensure_parent() -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _compute_checksum(payload: dict[str, object]) -> str:
    digest = hashlib.sha256()
    for key in sorted(payload.keys()):
        value = payload.get(key)
        digest.update(f"{key}={value}".encode("utf-8"))
    return digest.hexdigest()


def _open_connection() -> sqlite3.Connection:
    _ensure_parent()
    conn = sqlite3.connect(LEDGER_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    for query in _SCHEMA_QUERIES:
        conn.execute(query)
    conn.commit()


def append_decision(
    *,
    auth_request_id: str,
    session_id: str,
    requester_user_id: int,
    reviewer_user_id: int,
    decision: str,
    note: str,
    recorded_at: Optional[datetime] = None,
) -> LedgerEntry:
    recorded_at = recorded_at or datetime.utcnow()
    checksum_payload = {
        "auth_request_id": auth_request_id,
        "session_id": session_id,
        "requester_user_id": requester_user_id,
        "reviewer_user_id": reviewer_user_id,
        "decision": decision,
        "note": note,
        "timestamp": recorded_at.isoformat(),
    }
    checksum = _compute_checksum(checksum_payload)

    with _lock:
        with _open_connection() as conn:
            conn.execute(
                """
                INSERT INTO decisions (
                    auth_request_id,
                    session_id,
                    requester_user_id,
                    reviewer_user_id,
                    decision,
                    note,
                    created_at,
                    checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    auth_request_id,
                    session_id,
                    requester_user_id,
                    reviewer_user_id,
                    decision,
                    note,
                    recorded_at.isoformat(),
                    checksum,
                ),
            )
            conn.commit()

    return LedgerEntry(
        auth_request_id=auth_request_id,
        session_id=session_id,
        requester_user_id=requester_user_id,
        reviewer_user_id=reviewer_user_id,
        decision=decision,
        note=note,
        created_at=recorded_at,
        checksum=checksum,
    )


def iter_decisions(limit: Optional[int] = None) -> Iterable[LedgerEntry]:
    with _lock:
        with _open_connection() as conn:
            stmt = "SELECT auth_request_id, session_id, requester_user_id, reviewer_user_id, decision, note, created_at, checksum FROM decisions ORDER BY id DESC"
            if limit is not None:
                stmt += f" LIMIT {int(limit)}"
            cursor = conn.execute(stmt)
            rows = cursor.fetchall()
    for row in rows:
        yield LedgerEntry(
            auth_request_id=row[0],
            session_id=row[1],
            requester_user_id=row[2],
            reviewer_user_id=row[3],
            decision=row[4],
            note=row[5] or "",
            created_at=datetime.fromisoformat(row[6]),
            checksum=row[7],
        )


def latest_checksum() -> Optional[str]:
    with _lock:
        with _open_connection() as conn:
            cursor = conn.execute("SELECT checksum FROM decisions ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
    if not row:
        return None
    return row[0]
