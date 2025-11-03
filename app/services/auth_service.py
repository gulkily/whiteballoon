from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.config import get_settings
from app.models import (
    AuthApproval,
    AuthRequestStatus,
    AuthenticationRequest,
    InviteToken,
    User,
    UserSession,
)
from app.modules.requests import services as request_services
from app.services import user_attribute_service

SESSION_COOKIE_NAME = "wb_session_id"


def normalize_username(username: str) -> str:
    cleaned = username.strip().lower()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username required")
    if " " in cleaned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username cannot contain spaces")
    return cleaned


def create_user_with_invite(
    session: Session,
    *,
    username: str,
    contact_email: Optional[str],
    invite_token: Optional[str],
) -> User:
    normalized = normalize_username(username)

    existing_user = session.exec(select(User).where(User.username == normalized)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user_count = session.exec(select(User).limit(1)).first()

    if user_count and not invite_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token required")

    if invite_token:
        token_record = session.get(InviteToken, invite_token)
        if not token_record or token_record.disabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invite token")
        if token_record.expires_at and token_record.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token expired")
        if token_record.use_count >= token_record.max_uses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token fully used")
    else:
        token_record = None

    new_user = User(
        username=normalized,
        contact_email=contact_email,
        is_admin=False,
    )

    if user_count is None:
        # First user becomes admin automatically.
        new_user.is_admin = True

    session.add(new_user)
    session.flush()

    if token_record:
        token_record.use_count += 1
        inviter_id = token_record.created_by_user_id
        if inviter_id:
            user_attribute_service.set_attribute(
                session,
                user_id=new_user.id,
                key=user_attribute_service.INVITED_BY_USER_ID_KEY,
                value=str(inviter_id),
                actor_user_id=inviter_id,
            )
        user_attribute_service.set_attribute(
            session,
            user_id=new_user.id,
            key=user_attribute_service.INVITE_TOKEN_USED_KEY,
            value=token_record.token,
            actor_user_id=inviter_id,
        )

    session.commit()
    session.refresh(new_user)
    return new_user


def create_invite_token(session: Session, *, created_by: Optional[User], max_uses: int = 1, expires_in_days: Optional[int] = None) -> InviteToken:
    invite = InviteToken(
        created_by_user_id=created_by.id if created_by else None,
        max_uses=max_uses,
    )
    if expires_in_days:
        invite.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    session.add(invite)
    session.commit()
    session.refresh(invite)
    return invite


def create_auth_request(
    session: Session,
    *,
    user: User,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> tuple[AuthenticationRequest, UserSession]:
    # Expire older requests that have passed their window
    now = datetime.utcnow()
    for auth_request in session.exec(
        select(AuthenticationRequest).where(
            AuthenticationRequest.user_id == user.id,
            AuthenticationRequest.status == AuthRequestStatus.pending,
        )
    ):
        if auth_request.expires_at < now:
            auth_request.status = AuthRequestStatus.expired

    auth_request = AuthenticationRequest(
        user_id=user.id,
        device_info=user_agent,
        ip_address=ip_address,
    )
    session.add(auth_request)
    session.flush()

    settings = get_settings()
    session_record = UserSession(
        user_id=user.id,
        auth_request_id=auth_request.id,
        expires_at=now + timedelta(minutes=settings.session_expiry_minutes),
        is_fully_authenticated=False,
    )
    session.add(session_record)
    session.commit()
    session.refresh(auth_request)
    session.refresh(session_record)
    return auth_request, session_record


def approve_auth_request(
    session: Session,
    *,
    auth_request: AuthenticationRequest,
    approver: Optional[User] = None,
) -> AuthenticationRequest:
    if auth_request.status != AuthRequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request not pending")

    auth_request.status = AuthRequestStatus.approved
    if approver:
        approval = AuthApproval(auth_request_id=auth_request.id, approver_user_id=approver.id)
        session.add(approval)

    session_records = session.exec(
        select(UserSession).where(UserSession.auth_request_id == auth_request.id)
    ).all()
    for session_record in session_records:
        session_record.is_fully_authenticated = True

    session.commit()

    # Promote any pending requests now that the user is fully authenticated.
    request_services.promote_pending_requests(session, user_id=auth_request.user_id)

    session.refresh(auth_request)
    return auth_request


def find_pending_auth_request(session: Session, *, username: str, verification_code: str) -> AuthenticationRequest:
    normalized = normalize_username(username)
    auth_request = session.exec(
        select(AuthenticationRequest)
        .join(User)
        .where(
            User.username == normalized,
            AuthenticationRequest.verification_code == verification_code.strip().upper(),
        )
    ).first()

    if not auth_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification code not found")

    if auth_request.status != AuthRequestStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already processed")

    if auth_request.expires_at < datetime.utcnow():
        auth_request.status = AuthRequestStatus.expired
        session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")

    return auth_request


def revoke_session(session: Session, *, session_id: str) -> None:
    record = session.get(UserSession, session_id)
    if record:
        session.delete(record)
        session.commit()


def touch_session(session: Session, *, session_record: UserSession) -> None:
    session_record.last_seen_at = datetime.utcnow()
    session.commit()
