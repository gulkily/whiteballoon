from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import select

from app.config import get_settings
from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import User
from app.services import auth_service
from app.modules.messaging import services
from app.routes.ui.helpers import describe_session_role, templates

router = APIRouter(prefix="/messages", tags=["messages"])


def _require_messaging_enabled() -> None:
    if not get_settings().messaging_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Messaging disabled")


def _ensure_fully_authenticated(session_user: SessionUser) -> None:
    if not session_user.session.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full membership required")


def _base_context(request: Request, session_user: SessionUser) -> dict[str, object]:
    return {
        "request": request,
        "user": session_user.user,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "session_avatar_url": session_user.avatar_url,
    }


@router.get("")
def messaging_inbox(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    _: None = Depends(_require_messaging_enabled),
):
    _ensure_fully_authenticated(session_user)
    summaries = services.list_threads_for_user(session_user.user.id)
    counterpart_ids: set[int] = set()
    viewer_id = session_user.user.id
    for summary in summaries:
        for participant in summary.participants:
            if participant.user_id and participant.user_id != viewer_id:
                counterpart_ids.add(participant.user_id)
    user_map: dict[int, User] = {}
    if counterpart_ids:
        rows = db.exec(select(User).where(User.id.in_(list(counterpart_ids)))).all()
        user_map = {row.id: row for row in rows}
    thread_entries: list[dict[str, object]] = []
    for summary in summaries:
        viewer_participant = next((p for p in summary.participants if p.user_id == viewer_id), None)
        other_participant = next((p for p in summary.participants if p.user_id != viewer_id), None)
        counterpart_user = user_map.get(other_participant.user_id) if other_participant else None  # type: ignore[arg-type]
        thread_entries.append(
            {
                "thread": summary.thread,
                "viewer_participant": viewer_participant,
                "counterpart": counterpart_user,
                "last_message": summary.last_message,
            }
        )
    context = _base_context(request, session_user)
    context.update(
        {
            "threads": thread_entries,
            "has_threads": bool(thread_entries),
        }
    )
    return templates.TemplateResponse("messaging/inbox.html", context)


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


@router.get("/with/{username}")
def open_thread_with_username(
    username: str,
    db: SessionDep,
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
    return RedirectResponse(url=f"/messages/{thread.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{thread_id}")
def view_thread(
    thread_id: int,
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    _: None = Depends(_require_messaging_enabled),
):
    _ensure_fully_authenticated(session_user)
    detail = services.load_thread_for_user(session_user.user.id, thread_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found.")
    participant_ids = [p.user_id for p in detail.participants if p.user_id != session_user.user.id]
    user_map: dict[int, User] = {}
    if participant_ids:
        rows = db.exec(select(User).where(User.id.in_(participant_ids))).all()
        user_map = {row.id: row for row in rows}
    messages: list[dict[str, object]] = []
    for message in detail.messages:
        sender = user_map.get(message.sender_user_id) or (session_user.user if message.sender_user_id == session_user.user.id else None)
        messages.append(
            {
                "record": message,
                "sender": sender,
                "is_self": message.sender_user_id == session_user.user.id,
            }
        )
    counterpart = None
    for participant in detail.participants:
        if participant.user_id != session_user.user.id:
            counterpart = user_map.get(participant.user_id)
            break
    services.mark_thread_read(session_user.user.id, thread_id)
    context = _base_context(request, session_user)
    context.update(
        {
            "thread": detail.thread,
            "messages": messages,
            "counterpart": counterpart,
            "viewer_participant": detail.viewer_participant,
        }
    )
    return templates.TemplateResponse("messaging/thread.html", context)


__all__ = ["router"]
