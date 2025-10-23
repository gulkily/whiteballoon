from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.dependencies import SessionDep, apply_session_cookie, get_current_session, require_admin
from app.models import AuthenticationRequest, AuthApproval, User, UserSession
from app.modules.requests import services as request_services
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    username: str
    contact_email: Optional[str] = None
    invite_token: Optional[str] = None
    initial_request: Optional[str] = None


class LoginPayload(BaseModel):
    username: str


class VerifyPayload(BaseModel):
    username: str
    verification_code: str


class InvitePayload(BaseModel):
    max_uses: int = 1
    expires_in_days: Optional[int] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterPayload, db: SessionDep) -> dict:
    user = auth_service.create_user_with_invite(
        db,
        username=payload.username,
        contact_email=payload.contact_email,
        invite_token=payload.invite_token,
    )

    if payload.initial_request and payload.initial_request.strip():
        request_services.create_request(
            db,
            user=user,
            description=payload.initial_request,
            contact_email=payload.contact_email,
        )

    return {"username": user.username, "is_admin": user.is_admin}


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(
    payload: LoginPayload,
    response: Response,
    request: Request,
    db: SessionDep,
) -> dict:
    normalized = auth_service.normalize_username(payload.username)

    user = db.exec(select(User).where(User.username == normalized)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    auth_request, session_record = auth_service.create_auth_request(
        db,
        user=user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    apply_session_cookie(response, session_record)

    return {
        "auth_request_id": auth_request.id,
        "verification_code": auth_request.verification_code,
        "status": auth_request.status.value,
    }


@router.post("/login/verify", status_code=status.HTTP_200_OK)
def verify_login(payload: VerifyPayload, db: SessionDep, response: Response) -> dict:
    auth_request = auth_service.find_pending_auth_request(
        db,
        username=payload.username,
        verification_code=payload.verification_code,
    )

    auth_service.approve_auth_request(db, auth_request=auth_request, approver=None)

    session_record = db.exec(
        select(UserSession).where(UserSession.auth_request_id == auth_request.id)
    ).first()
    if not session_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session missing")

    apply_session_cookie(response, session_record)

    return {"status": auth_request.status.value}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, db: SessionDep, session_record: Optional[UserSession] = Depends(get_current_session)) -> None:
    if session_record:
        auth_service.revoke_session(db, session_id=session_record.id)
    response.delete_cookie(auth_service.SESSION_COOKIE_NAME, path="/")


@router.post("/invites", status_code=status.HTTP_201_CREATED)
def create_invite(
    payload: dict,
    db: SessionDep,
    admin: User = Depends(require_admin),
) -> dict:
    max_uses = int(payload.get("max_uses", 1))
    expires_in_days = payload.get("expires_in_days")
    expires = int(expires_in_days) if expires_in_days is not None else None

    invite = auth_service.create_invite_token(
        db,
        created_by=admin,
        max_uses=max(max_uses, 1),
        expires_in_days=expires,
    )
    return {"token": invite.token, "max_uses": invite.max_uses, "expires_at": invite.expires_at}


@router.get("/requests/{auth_request_id}")
def get_auth_request_status(auth_request_id: str, db: SessionDep, user: User = Depends(require_admin)) -> dict:
    auth_request = db.get(AuthenticationRequest, auth_request_id)
    if not auth_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auth request not found")

    approvals = db.exec(
        select(AuthApproval).where(AuthApproval.auth_request_id == auth_request.id)
    ).all()

    return {
        "status": auth_request.status.value,
        "verification_code": auth_request.verification_code,
        "approvals": [approval.approver_user_id for approval in approvals],
    }
