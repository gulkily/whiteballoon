from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import SessionUser, require_session_user
from app.services import comment_llm_insights_service

router = APIRouter(prefix="/api/admin/comment-insights", tags=["comment-insights"])


def _require_admin(session_user: SessionUser) -> None:
    if not session_user.user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("/comments/{comment_id}")
def fetch_comment_insight(
    comment_id: int,
    session_user: SessionUser = Depends(require_session_user),
) -> dict:
    _require_admin(session_user)
    insight = comment_llm_insights_service.get_analysis_by_comment_id(comment_id)
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment analysis not found")
    return insight.to_dict()


@router.get("/runs")
def list_runs(
    limit: int = Query(default=20, ge=1, le=200),
    session_user: SessionUser = Depends(require_session_user),
) -> dict:
    _require_admin(session_user)
    runs = [run.to_dict() for run in comment_llm_insights_service.list_recent_runs(limit=limit)]
    return {"runs": runs}


@router.get("/runs/{run_id}/analyses")
def list_analyses_for_run(
    run_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    session_user: SessionUser = Depends(require_session_user),
) -> dict:
    _require_admin(session_user)
    items = [insight.to_dict() for insight in comment_llm_insights_service.list_analyses_for_run(run_id, limit=limit)]
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found or has no analyses")
    return {"analyses": items}
