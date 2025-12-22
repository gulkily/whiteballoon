from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.config import get_settings
from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates
from app.services import peer_auth_ledger, peer_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["peer-auth"])


def _ensure_reviewer(
    db: SessionDep,
    session_user: SessionUser,
) -> SessionUser:
    viewer = session_user.user
    if not get_settings().feature_peer_auth_queue:
        logger.info(
            "Peer auth queue blocked for user %s because feature flag is disabled",
            viewer.id,
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Peer authentication queue disabled")

    if not viewer.is_admin and not session_user.session.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full membership required")

    peer_auth_service.require_peer_auth_reviewer(db, user=viewer)
    return session_user


def _redirect_to_inbox(
    request: Request,
    *,
    status_label: Optional[str] = None,
    error_message: Optional[str] = None,
    auth_request_id: Optional[str] = None,
) -> RedirectResponse:
    base_url = request.url_for("peer_auth_inbox")
    params: dict[str, str] = {}
    if status_label:
        params["status"] = status_label
    if error_message:
        params["error"] = error_message
    if auth_request_id:
        params["request_id"] = auth_request_id
    target = str(base_url)
    if params:
        target = f"{base_url}?{urlencode(params)}"
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/peer-auth")
def peer_auth_inbox(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    session_user = _ensure_reviewer(db, session_user)
    viewer = session_user.user

    summaries = peer_auth_service.list_peer_auth_sessions(db, limit=25, pending_only=True)
    pending_count = peer_auth_service.count_peer_auth_sessions(db, pending_only=True)
    status_label = request.query_params.get("status")
    recent_request_id = request.query_params.get("request_id")
    error_message = request.query_params.get("error")
    status_message = None
    if status_label == "approved" and recent_request_id:
        status_message = f"Approved session {recent_request_id}."
    elif status_label == "denied" and recent_request_id:
        status_message = f"Denied session {recent_request_id}."

    context = {
        "request": request,
        "user": viewer,
        "session": session_user.session,
        "session_role": describe_session_role(viewer, session_user.session),
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "peer_auth_sessions": summaries,
        "peer_auth_pending_count": pending_count,
        "peer_auth_status_message": status_message,
        "peer_auth_error_message": error_message,
        "feature_peer_auth_queue": get_settings().feature_peer_auth_queue,
    }
    return templates.TemplateResponse("peer_auth/index.html", context)


def _serialize_summary(summary):
    return {
        "auth_request_id": summary.auth_request_id,
        "session_id": summary.session_id,
        "username": summary.username,
        "status": summary.status.value,
        "verification_code": summary.verification_code,
        "session_last_seen_at": summary.session_last_seen_at.isoformat() if summary.session_last_seen_at else None,
        "auth_request_created_at": summary.auth_request_created_at.isoformat() if summary.auth_request_created_at else None,
        "ip_address": summary.ip_address,
        "device_info": summary.device_info,
    }


@router.get("/peer-auth/notifications")
def peer_auth_notifications(
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    session_user = _ensure_reviewer(db, session_user)
    pending_count = peer_auth_service.count_peer_auth_sessions(db, pending_only=True)
    next_request = None
    if pending_count > 0:
        summaries = peer_auth_service.list_peer_auth_sessions(db, limit=1, pending_only=True)
        if summaries:
            summary = summaries[0]
            next_request = {
                "username": summary.username,
                "requested_at": summary.auth_request_created_at.isoformat() if summary.auth_request_created_at else None,
            }

    return {
        "pending_count": pending_count,
        "next_request": next_request,
    }


@router.get("/peer-auth/refresh")
def peer_auth_refresh(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    session_user = _ensure_reviewer(db, session_user)
    summaries = peer_auth_service.list_peer_auth_sessions(db, limit=25, pending_only=True)
    pending_count = peer_auth_service.count_peer_auth_sessions(db, pending_only=True)
    template = templates.get_template("peer_auth/partials/list.html")
    html = template.render(
        {
            "request": request,
            "peer_auth_sessions": summaries,
        }
    )
    return {
        "pending_count": pending_count,
        "html": html,
        "sessions": [_serialize_summary(summary) for summary in summaries],
    }


@router.post("/peer-auth/{auth_request_id}/approve")
def peer_auth_approve(
    request: Request,
    auth_request_id: str,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    attestation_note: Optional[str] = Form(default=None),
):
    session_user = _ensure_reviewer(db, session_user)
    viewer = session_user.user
    try:
        decision = peer_auth_service.approve_peer_auth_request(
            db,
            auth_request_id=auth_request_id,
            reviewer=viewer,
            note=attestation_note,
        )
    except HTTPException as exc:
        if exc.status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND}:
            return _redirect_to_inbox(
                request,
                error_message=str(exc.detail),
                auth_request_id=auth_request_id,
            )
        raise

    peer_auth_ledger.append_decision(
        auth_request_id=decision.auth_request_id,
        session_id=decision.session_id,
        requester_user_id=decision.requester_user_id,
        reviewer_user_id=decision.reviewer_user_id,
        decision=decision.decision,
        note=decision.note,
    )
    logger.info(
        "Peer auth %s request %s by reviewer %s",
        decision.decision,
        decision.auth_request_id,
        viewer.id,
    )

    return _redirect_to_inbox(
        request,
        status_label="approved",
        auth_request_id=auth_request_id,
    )


@router.post("/peer-auth/{auth_request_id}/deny")
def peer_auth_deny(
    request: Request,
    auth_request_id: str,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    attestation_note: Optional[str] = Form(default=None),
):
    session_user = _ensure_reviewer(db, session_user)
    viewer = session_user.user
    try:
        decision = peer_auth_service.deny_peer_auth_request(
            db,
            auth_request_id=auth_request_id,
            reviewer=viewer,
            note=attestation_note,
        )
    except HTTPException as exc:
        if exc.status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND}:
            return _redirect_to_inbox(
                request,
                error_message=str(exc.detail),
                auth_request_id=auth_request_id,
            )
        raise

    peer_auth_ledger.append_decision(
        auth_request_id=decision.auth_request_id,
        session_id=decision.session_id,
        requester_user_id=decision.requester_user_id,
        reviewer_user_id=decision.reviewer_user_id,
        decision=decision.decision,
        note=decision.note,
    )
    logger.info(
        "Peer auth %s request %s by reviewer %s",
        decision.decision,
        decision.auth_request_id,
        viewer.id,
    )

    return _redirect_to_inbox(
        request,
        status_label="denied",
        auth_request_id=auth_request_id,
    )
