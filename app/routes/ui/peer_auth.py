from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates
from app.services import peer_auth_ledger, peer_auth_service

router = APIRouter(tags=["peer-auth"])


def _ensure_reviewer(
    db: SessionDep,
    session_user: SessionUser,
) -> SessionUser:
    viewer = session_user.user
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
    }
    return templates.TemplateResponse("peer_auth/index.html", context)


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

    return _redirect_to_inbox(
        request,
        status_label="denied",
        auth_request_id=auth_request_id,
    )
