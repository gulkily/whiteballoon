from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
import logging
from sqlmodel import Session, select

from app.config import get_settings
from app.models import (
    AuthApproval,
    AuthRequestStatus,
    AuthenticationRequest,
    InvitePersonalization,
    InviteToken,
    User,
    UserSession,
)
from app.modules.requests import services as request_services
from app.services import user_attribute_service

SESSION_COOKIE_NAME = "wb_session_id"
logger = logging.getLogger(__name__)


@dataclass
class RegistrationResult:
    user: User
    session: Optional[UserSession]
    auto_approved: bool


@dataclass
class InvitePersonalizationPayload:
    photo_url: str
    gratitude_note: str
    support_message: str
    help_examples: List[str]
    fun_details: str


@dataclass
class InviteCreationResult:
    invite: InviteToken
    personalization: Optional[InvitePersonalization]


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
) -> RegistrationResult:
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

    auto_approved = False
    session_record: Optional[UserSession] = None

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

        if token_record.auto_approve:
            auto_approved = True
    else:
        # First user (no invite) becomes admin and should be fully authenticated immediately.
        auto_approved = True

    if auto_approved:
        now = datetime.utcnow()
        settings = get_settings()
        session_record = UserSession(
            user_id=new_user.id,
            is_fully_authenticated=True,
            expires_at=now + timedelta(minutes=settings.session_expiry_minutes),
        )
        session.add(session_record)

    session.commit()
    session.refresh(new_user)
    if session_record:
        session.refresh(session_record)

    if auto_approved:
        logger.info(
            "Auto-approved registration",
            extra={
                "user_id": new_user.id,
                "username": new_user.username,
                "invite_token": token_record.token if token_record else None,
            },
        )

    return RegistrationResult(user=new_user, session=session_record, auto_approved=auto_approved)


def create_invite_token(
    session: Session,
    *,
    created_by: Optional[User],
    max_uses: int = 1,
    expires_in_days: Optional[int] = None,
    auto_approve: bool = True,
    suggested_username: Optional[str] = None,
    suggested_bio: Optional[str] = None,
    personalization: Optional[InvitePersonalizationPayload] = None,
) -> InviteCreationResult:
    invite = InviteToken(
        created_by_user_id=created_by.id if created_by else None,
        max_uses=max_uses,
        auto_approve=auto_approve,
        suggested_username=(suggested_username.strip() if suggested_username else None),
        suggested_bio=(suggested_bio.strip() if suggested_bio else None),
    )
    if expires_in_days:
        invite.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    session.add(invite)

    personalization_record: Optional[InvitePersonalization] = None
    if personalization:
        personalization_record = InvitePersonalization(
            token=invite.token,
            photo_url=personalization.photo_url.strip(),
            gratitude_note=personalization.gratitude_note.strip(),
            support_message=personalization.support_message.strip(),
            help_examples="\n".join(item.strip() for item in personalization.help_examples if item.strip()),
            fun_details=personalization.fun_details.strip(),
        )
        session.add(personalization_record)

    session.commit()
    session.refresh(invite)
    if personalization_record:
        session.refresh(personalization_record)
    return InviteCreationResult(invite=invite, personalization=personalization_record)


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


def get_invite_personalization(session: Session, token: str) -> Optional[InvitePersonalization]:
    return session.get(InvitePersonalization, token)


def serialize_invite_personalization(record: Optional[InvitePersonalization]) -> Optional[dict[str, object]]:
    if not record:
        return None
    help_examples = []
    if record.help_examples:
        help_examples = [item for item in record.help_examples.splitlines() if item]

    return {
        "photo_url": record.photo_url,
        "gratitude_note": record.gratitude_note,
        "support_message": record.support_message,
        "help_examples": help_examples,
        "fun_details": record.fun_details,
    }


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
