from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates
from app.services import peer_auth_service

router = APIRouter(tags=["peer-auth"])


@router.get("/peer-auth")
def peer_auth_inbox(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    viewer = session_user.user
    if not viewer.is_admin and not session_user.session.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full membership required")

    peer_auth_service.require_peer_auth_reviewer(db, user=viewer)

    summaries = peer_auth_service.list_peer_auth_sessions(db, limit=25, pending_only=True)
    pending_count = peer_auth_service.count_peer_auth_sessions(db, pending_only=True)

    context = {
        "request": request,
        "user": viewer,
        "session": session_user.session,
        "session_role": describe_session_role(viewer, session_user.session),
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "peer_auth_sessions": summaries,
        "peer_auth_pending_count": pending_count,
    }
    return templates.TemplateResponse("peer_auth/index.html", context)

