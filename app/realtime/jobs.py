from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from . import storage

JobState = str
_TERMINAL_STATES = {"success", "error", "warning"}
_EXPIRY_WINDOW = timedelta(hours=24)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobEnvelope:
    id: str
    category: str
    target: Dict[str, Any]
    state: JobState = "queued"
    phase: Optional[str] = None
    progress: Optional[float] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    structured_data: Dict[str, Any] = field(default_factory=dict)
    queued_at: datetime = field(default_factory=_now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_now)
    triggered_by: Optional[str] = None
    viewer_scope: Dict[str, Any] = field(default_factory=lambda: {"admin_only": True})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "target": dict(self.target),
            "state": self.state,
            "phase": self.phase,
            "progress": self.progress,
            "message": self.message,
            "error_code": self.error_code,
            "structured_data": dict(self.structured_data),
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "updated_at": self.updated_at,
            "triggered_by": self.triggered_by,
            "viewer_scope": dict(self.viewer_scope),
        }


_LOCK = Lock()
_REGISTRY: Dict[str, JobEnvelope] = {}


def enqueue_job(
    *,
    category: str,
    target: Dict[str, Any] | None = None,
    triggered_by: Optional[str] = None,
    message: Optional[str] = None,
    viewer_scope: Optional[Dict[str, Any]] = None,
    structured_data: Optional[Dict[str, Any]] = None,
) -> JobEnvelope:
    job_id = uuid4().hex
    envelope = JobEnvelope(
        id=job_id,
        category=category,
        target=target or {},
        message=message,
        triggered_by=triggered_by,
        structured_data=structured_data or {},
        viewer_scope=viewer_scope or {"admin_only": True},
    )
    with _LOCK:
        _REGISTRY[job_id] = envelope
        snapshot = JobEnvelope(**envelope.to_dict())
    _persist_job(snapshot)
    return envelope


def update_job(job_id: str, **fields: Any) -> JobEnvelope:
    with _LOCK:
        job = _REGISTRY.get(job_id)
        if not job:
            raise KeyError(f"Unknown job id '{job_id}'")
        state = fields.get("state")
        structured = fields.pop("structured_data", None)
        target = fields.pop("target", None)
        for key, value in fields.items():
            setattr(job, key, value)
        if structured is not None:
            job.structured_data.update(structured)
        if target is not None:
            job.target.update(target)
        now = _now()
        if state:
            job.state = state
            if state == "running" and job.started_at is None:
                job.started_at = now
            if state in _TERMINAL_STATES and job.finished_at is None:
                job.finished_at = now
        job.updated_at = now
        snapshot = JobEnvelope(**job.to_dict())
    _persist_job(snapshot)
    return job


def get_job(job_id: str) -> Optional[JobEnvelope]:
    with _LOCK:
        _prune_locked()
        job = _REGISTRY.get(job_id)
        if not job:
            return None
        return JobEnvelope(**job.to_dict())


def list_jobs(job_ids: Optional[Iterable[str]] = None) -> List[JobEnvelope]:
    with _LOCK:
        _prune_locked()
        if job_ids is None:
            jobs = list(_REGISTRY.values())
        else:
            scope = set(job_ids)
            jobs = [job for job_id, job in _REGISTRY.items() if job_id in scope]
        return [JobEnvelope(**job.to_dict()) for job in jobs]


def serialize_job(job: JobEnvelope) -> Dict[str, Any]:
    data = job.to_dict()
    for key in ("queued_at", "started_at", "finished_at", "updated_at"):
        value = data.get(key)
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


def load_job_history(limit: Optional[int] = None) -> List[dict[str, Any]]:
    return storage.load_history(limit)


def _persist_job(job: JobEnvelope) -> None:
    try:
        storage.persist_snapshot(serialize_job(job))
    except OSError:
        # Persistence failures should not stop realtime updates.
        pass


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None


def _envelope_from_snapshot(snapshot: Dict[str, Any]) -> JobEnvelope:
    return JobEnvelope(
        id=str(snapshot.get("id") or uuid4().hex),
        category=str(snapshot.get("category") or "unknown"),
        target=dict(snapshot.get("target") or {}),
        state=str(snapshot.get("state") or "queued"),
        phase=snapshot.get("phase"),
        progress=snapshot.get("progress"),
        message=snapshot.get("message"),
        error_code=snapshot.get("error_code"),
        structured_data=dict(snapshot.get("structured_data") or {}),
        queued_at=_parse_datetime(snapshot.get("queued_at")) or _now(),
        started_at=_parse_datetime(snapshot.get("started_at")),
        finished_at=_parse_datetime(snapshot.get("finished_at")),
        updated_at=_parse_datetime(snapshot.get("updated_at")) or _now(),
        triggered_by=snapshot.get("triggered_by"),
        viewer_scope=dict(snapshot.get("viewer_scope") or {"admin_only": True}),
    )


def _bootstrap_from_storage() -> None:
    snapshots = storage.load_history(limit=None)
    if not snapshots:
        return
    latest: Dict[str, Dict[str, Any]] = {}
    for snapshot in snapshots:
        job_id = snapshot.get("id")
        if not job_id:
            continue
        latest[str(job_id)] = snapshot
    now = _now()
    with _LOCK:
        for snapshot in latest.values():
            job = _envelope_from_snapshot(snapshot)
            if job.finished_at and now - job.finished_at > _EXPIRY_WINDOW:
                continue
            _REGISTRY[job.id] = job


_bootstrap_from_storage()


def _prune_locked() -> None:
    if not _REGISTRY:
        return
    now = _now()
    expired = [
        job_id
        for job_id, job in _REGISTRY.items()
        if job.finished_at and now - job.finished_at > _EXPIRY_WINDOW
    ]
    for job_id in expired:
        _REGISTRY.pop(job_id, None)


__all__ = [
    "JobEnvelope",
    "enqueue_job",
    "get_job",
    "list_jobs",
    "load_job_history",
    "serialize_job",
    "update_job",
    "reset",
]


def reset() -> None:
    with _LOCK:
        _REGISTRY.clear()
    storage.reset_history()
