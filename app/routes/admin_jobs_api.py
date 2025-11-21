from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.dependencies import SessionUser, require_session_user
from app.realtime import get_job as realtime_get_job
from app.realtime import list_jobs as realtime_list_jobs
from app.realtime import load_job_history as realtime_load_history
from app.realtime import serialize_job as realtime_serialize_job

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])


def _ensure_admin(session_user: SessionUser) -> None:
    if not session_user.user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("")
def list_recent_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    session_user: SessionUser = Depends(require_session_user),
) -> dict:
    _ensure_admin(session_user)
    snapshots = realtime_load_history(limit)
    return {"jobs": snapshots}


@router.get("/{job_id}")
def fetch_job(job_id: str, session_user: SessionUser = Depends(require_session_user)) -> dict:
    _ensure_admin(session_user)
    job = realtime_get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return realtime_serialize_job(job)


@router.get("/events")
async def stream_job_updates(
    request: Request,
    job_id: Optional[List[str]] = Query(default=None),
    session_user: SessionUser = Depends(require_session_user),
) -> StreamingResponse:
    _ensure_admin(session_user)
    job_scope: Optional[Iterable[str]] = job_id if job_id else None

    async def event_source():
        last_sent: dict[str, datetime] = {}
        heartbeat_deadline = time.monotonic()
        heartbeat_interval = 15.0
        while True:
            if await request.is_disconnected():
                break
            jobs = realtime_list_jobs(job_scope)
            for job in jobs:
                updated = job.updated_at
                previous = last_sent.get(job.id)
                if not previous or updated > previous:
                    last_sent[job.id] = updated
                    payload = json.dumps(realtime_serialize_job(job))
                    yield f"event: job-update\ndata: {payload}\n\n"
            now = time.monotonic()
            if now - heartbeat_deadline >= heartbeat_interval:
                heartbeat_deadline = now
                yield "event: heartbeat\ndata: {}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_source(), media_type="text/event-stream")
