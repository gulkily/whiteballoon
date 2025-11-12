from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobStatus:
    peer: str
    action: str
    queued_at: datetime = field(default_factory=_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: str = "queued"
    message: str | None = None
    triggered_by: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "peer": self.peer,
            "action": self.action,
            "queued_at": self.queued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "message": self.message,
            "triggered_by": self.triggered_by,
        }


_LOCK = Lock()
_JOBS: Dict[Tuple[str, str], JobStatus] = {}


def queue_job(peer: str, action: str, *, triggered_by: str | None = None) -> JobStatus:
    job = JobStatus(peer=peer, action=action, triggered_by=triggered_by)
    with _LOCK:
        _JOBS[(peer, action)] = job
    return job


def mark_started(peer: str, action: str) -> None:
    with _LOCK:
        job = _JOBS.get((peer, action))
        if not job:
            job = JobStatus(peer=peer, action=action)
            _JOBS[(peer, action)] = job
        job.started_at = _now()
        job.status = "running"


def mark_finished(peer: str, action: str, success: bool, message: str | None = None) -> None:
    with _LOCK:
        job = _JOBS.get((peer, action))
        if not job:
            job = JobStatus(peer=peer, action=action)
            _JOBS[(peer, action)] = job
        job.finished_at = _now()
        job.status = "success" if success else "error"
        job.message = message


def snapshot() -> dict[str, dict[str, JobStatus]]:
    with _LOCK:
        data: dict[str, dict[str, JobStatus]] = {}
        for (peer, action), job in _JOBS.items():
            data.setdefault(peer, {})[action] = job
        return data


__all__ = [
    "JobStatus",
    "queue_job",
    "mark_started",
    "mark_finished",
    "snapshot",
    "reset",
]


def reset() -> None:
    with _LOCK:
        _JOBS.clear()
