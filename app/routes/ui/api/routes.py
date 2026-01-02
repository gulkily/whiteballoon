from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.dependencies import SessionUser, require_session_user

router = APIRouter(tags=["ui"])
logger = logging.getLogger(__name__)


@router.post("/api/metrics")
async def ingest_metric(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    try:
        payload = await request.json()
    except Exception:  # pragma: no cover - malformed bodies
        raise HTTPException(status_code=400, detail="Invalid payload")

    category = str(payload.get("category", "")).strip().lower()
    event = str(payload.get("event", "")).strip().lower()
    if not category or not event:
        raise HTTPException(status_code=400, detail="category and event required")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    sanitized_metadata = {str(key): str(value) for key, value in metadata.items()}
    subject_id = payload.get("subject_id")
    logger.info(
        "metric_event",
        extra={
            "category": category,
            "event": event,
            "viewer_id": session_user.user.id,
            "subject_id": subject_id,
            "metadata": sanitized_metadata,
        },
    )
    return JSONResponse({"ok": True})
