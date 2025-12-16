from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.services import caption_preference_service

router = APIRouter(prefix="/api/captions", tags=["captions"])


@router.post("/{caption_id}/dismiss")
def dismiss_caption(
    caption_id: str,
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    if not caption_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid caption id")
    caption_preference_service.dismiss_caption(
        db,
        user_id=session_user.user.id,
        caption_id=caption_id,
        actor_user_id=session_user.user.id,
    )
    return {"status": "ok", "caption_id": caption_id}


__all__ = ["router"]
