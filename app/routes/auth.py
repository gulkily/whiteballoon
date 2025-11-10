from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlmodel import Session, select

from app.dependencies import (
    SessionDep,
    SessionUser,
    apply_session_cookie,
    get_current_session,
    require_admin,
    require_session_user,
)
from app.models import AuthenticationRequest, AuthApproval, User, UserSession
from app.modules.requests import services as request_services
from app.services import auth_service
from app.services.auth_service import InvitePersonalizationPayload
from app.url_utils import build_invite_link, generate_qr_code_data_url
from pathlib import Path

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
def register_user(payload: RegisterPayload, db: SessionDep, response: Response) -> dict:
    registration = auth_service.create_user_with_invite(
        db,
        username=payload.username,
        contact_email=payload.contact_email,
        invite_token=payload.invite_token,
    )

    if payload.initial_request and payload.initial_request.strip():
        request_services.create_request(
            db,
            user=registration.user,
            description=payload.initial_request,
            contact_email=payload.contact_email,
        )

    if registration.session:
        apply_session_cookie(response, registration.session)

    return {
        "username": registration.user.username,
        "is_admin": registration.user.is_admin,
        "auto_approved": registration.auto_approved,
    }


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


@router.post("/logout")
def logout(db: SessionDep, session_record: Optional[UserSession] = Depends(get_current_session)) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if session_record:
        auth_service.revoke_session(db, session_id=session_record.id)
    response.delete_cookie(auth_service.SESSION_COOKIE_NAME, path="/")
    return response


@router.post("/invites", status_code=status.HTTP_201_CREATED)
async def create_invite(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    suggested_username: str = Form(...),
    gratitude_note: str = Form(...),
    support_message: str = Form(...),
    fun_details: Optional[str] = Form(None),
    help_examples: Optional[List[str]] = Form(None),
    share_publicly: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    max_uses: int = Form(1),
    expires_in_days: Optional[int] = Form(None),
) -> dict:
    try:
        max_uses_value = max(1, int(max_uses))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="max_uses must be a number")

    expires = None
    if expires_in_days not in (None, ""):
        try:
            expires = int(expires_in_days)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="expires_in_days must be a number")

    personalization = _parse_personalization_payload(
        suggested_username=suggested_username,
        gratitude_note=gratitude_note,
        support_message=support_message,
        fun_details=fun_details,
        help_examples=help_examples,
    )

    photo_url = await _store_invite_photo(photo)
    sync_scope = "public" if share_publicly else "private"

    invite_result = auth_service.create_invite_token(
        db,
        created_by=session_user.user,
        max_uses=max_uses_value,
        expires_in_days=expires,
        suggested_username=personalization.pop("suggested_username"),
        suggested_bio=personalization.pop("suggested_bio"),
        personalization=InvitePersonalizationPayload(photo_url=photo_url, **personalization),
        sync_scope=sync_scope,
    )

    invite = invite_result.invite
    link = build_invite_link(invite.token, request)
    personalization_data = auth_service.serialize_invite_personalization(invite_result.personalization)
    if personalization_data is not None:
        personalization_data["suggested_username"] = invite.suggested_username or ""

    return {
        "token": invite.token,
        "max_uses": invite.max_uses,
        "expires_at": invite.expires_at,
        "link": link,
        "qr_code": generate_qr_code_data_url(link),
        "suggested_username": invite.suggested_username,
        "suggested_bio": invite.suggested_bio,
        "personalization": personalization_data,
    }


def _parse_personalization_payload(
    *,
    suggested_username: str,
    gratitude_note: str,
    support_message: str,
    fun_details: Optional[str],
    help_examples: Optional[List[str]],
) -> dict:
    def require_text(value: object, label: str, *, max_length: int = 512) -> str:
        if not isinstance(value, str):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{label} is required.")
        cleaned = value.strip()
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{label} is required.")
        if len(cleaned) > max_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{label} must be {max_length} characters or fewer.",
            )
        return cleaned

    normalized_username = auth_service.normalize_username(require_text(suggested_username, "Suggested username", max_length=64))
    gratitude = require_text(gratitude_note, "Gratitude note", max_length=600)
    support = require_text(support_message, "Support message", max_length=600)

    def optional_text(value: Optional[str], label: str, *, max_length: int) -> str:
        if not isinstance(value, str):
            return ""
        cleaned = value.strip()
        if len(cleaned) > max_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{label} must be {max_length} characters or fewer.",
            )
        return cleaned

    fun = optional_text(fun_details, "Fun details", max_length=600)

    cleaned_examples: List[str] = []
    if help_examples:
        for item in help_examples:
            if not isinstance(item, str):
                continue
            trimmed = item.strip()
            if not trimmed:
                continue
            if len(trimmed) > 240:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Help examples must be 240 characters or fewer each.",
                )
            cleaned_examples.append(trimmed)

    cleaned_examples = cleaned_examples[:3]

    lines = [
        "A note from your inviter:",
        gratitude,
        "\nHow they hope to support you:",
        support,
    ]
    if cleaned_examples:
        lines.append("\nWays they can help:")
        for example in cleaned_examples:
            lines.append(f"• {example}")
    if fun:
        lines.append("\nShared joys / inside jokes:")
        lines.append(fun)

    suggested_bio = "\n".join(lines).strip()

    return {
        "suggested_username": normalized_username,
        "suggested_bio": suggested_bio,
        "gratitude_note": gratitude,
        "support_message": support,
        "help_examples": cleaned_examples,
        "fun_details": fun,
    }


async def _store_invite_photo(upload: UploadFile) -> str:
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Photo file is required")

    suffix = Path(upload.filename).suffix.lower() or ".png"
    uploads_dir = Path("static/uploads/invite_photos")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    destination = uploads_dir / filename

    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Photo file is empty")

    destination.write_bytes(contents)
    return f"/static/uploads/invite_photos/{filename}"


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
