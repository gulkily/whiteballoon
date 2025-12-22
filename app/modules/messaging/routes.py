from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from sqlmodel import select

from app.config import get_settings
from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import User
from app.services import auth_service
from app.modules.messaging import services

router = APIRouter(prefix="/messages", tags=["messages"])


def _require_messaging_enabled() -> None:
    if not get_settings().messaging_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Messaging disabled")


def _ensure_fully_authenticated(session_user: SessionUser) -> None:
    if not session_user.session.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full membership required")


@router.get("")
def messaging_placeholder(
    session_user: SessionUser = Depends(require_session_user),
    _: None = Depends(_require_messaging_enabled),
):
    _ensure_fully_authenticated(session_user)
    return PlainTextResponse("Direct messaging inbox coming soon.")


@router.post("/direct")
def start_direct_conversation(
    request: Request,
    username: Annotated[str, Form(...)],
    db: SessionDep,
    next_url: Annotated[Optional[str], Form()] = None,
    session_user: SessionUser = Depends(require_session_user),
    _: None = Depends(_require_messaging_enabled),
):
    _ensure_fully_authenticated(session_user)
    normalized = auth_service.normalize_username(username)
    if normalized == session_user.user.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself.")
    target = db.exec(select(User).where(User.username == normalized)).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    thread = services.ensure_direct_thread(session_user.user.id, target.id)
    redirect_to = next_url or f"/messages/{thread.id}"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{thread_id}/messages")
def send_message_to_thread(
    request: Request,
    thread_id: int,
    body: Annotated[str, Form(...)],
    session_user: SessionUser = Depends(require_session_user),
    _: None = Depends(_require_messaging_enabled),
):
    _ensure_fully_authenticated(session_user)
    detail = services.load_thread_for_user(session_user.user.id, thread_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    recipients = [p for p in detail.participants if p.user_id != session_user.user.id]
    if not recipients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No recipient found.")
    target_id = recipients[0].user_id
    try:
        message, thread = services.send_direct_message(session_user.user.id, target_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    wants_json = "application/json" in (request.headers.get("accept") or "").lower()
    if wants_json:
        return JSONResponse(
            {
                "id": message.id,
                "thread_id": thread.id,
                "sender_id": message.sender_user_id,
                "body": message.body,
                "created_at": message.created_at.isoformat(),
            }
        )
    redirect_to = request.headers.get("referer") or f"/messages/{thread.id}"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


__all__ = ["router"]
