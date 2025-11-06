from __future__ import annotations

from typing import Annotated, Optional

from dataclasses import dataclass
from datetime import datetime

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.models import User, UserSession
from app.services import user_attribute_service
from app.services.auth_service import SESSION_COOKIE_NAME, touch_session
from starlette.responses import Response

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_session(
    db: SessionDep,
    request: Request,
    session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Optional[UserSession]:
    cookie_value = session_id or request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie_value:
        return None

    session_record = db.get(UserSession, cookie_value)
    if not session_record:
        return None

    if session_record.expires_at < datetime.utcnow():
        db.delete(session_record)
        db.commit()
        return None

    touch_session(db, session_record=session_record)
    return session_record


@dataclass
class SessionUser:
    user: User
    session: UserSession
    avatar_url: Optional[str]


def _get_profile_avatar_url(db: Session, user_id: int) -> Optional[str]:
    return user_attribute_service.get_attribute(
        db,
        user_id=user_id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )


def require_session_user(
    db: SessionDep,
    session_record: Annotated[Optional[UserSession], Depends(get_current_session)],
) -> SessionUser:
    if not session_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user = db.exec(select(User).where(User.id == session_record.user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    avatar_url = _get_profile_avatar_url(db, user.id)
    return SessionUser(user=user, session=session_record, avatar_url=avatar_url)


def require_authenticated_user(db: SessionDep, session_record: Annotated[Optional[UserSession], Depends(get_current_session)]) -> User:
    if not session_record or not session_record.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user = db.exec(select(User).where(User.id == session_record.user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(user: Annotated[User, Depends(require_authenticated_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


def apply_session_cookie(response: Response, session_record: UserSession) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_record.id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(settings.session_expiry_minutes * 60),
        path="/",
    )
