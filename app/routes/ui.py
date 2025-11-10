from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.dependencies import (
    SessionDep,
    SessionUser,
    apply_session_cookie,
    get_current_session,
    require_authenticated_user,
    require_session_user,
)
from app.models import AuthenticationRequest, InviteToken, User, UserSession
from app.modules.requests import services as request_services
from app.modules.requests.routes import RequestResponse, calculate_can_complete
from app.services import (
    auth_service,
    invite_graph_service,
    invite_map_cache_service,
    user_attribute_service,
)
from app.url_utils import build_invite_link, generate_qr_code_data_url

router = APIRouter(tags=["ui"])

templates = Jinja2Templates(directory="templates")


def _parse_iso_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def friendly_time(value: Union[str, datetime, None]) -> str:
    dt = _parse_iso_datetime(value)
    if dt is None:
        return ""

    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    seconds = int(delta.total_seconds())

    suffix = "ago"
    if seconds < 0:
        seconds = abs(seconds)
        suffix = "from now"

    if seconds < 45:
        return "just now" if suffix == "ago" else "in a moment"
    if seconds < 90:
        return f"1 minute {suffix}"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minutes {suffix}"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"

    days = hours // 24
    if days == 1:
        return "yesterday" if suffix == "ago" else "tomorrow"
    if days < 7:
        return f"{days} days {suffix}"

    weeks = days // 7
    if weeks < 5:
        return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"

    local_now = datetime.now().astimezone()
    local_dt = dt.astimezone(local_now.tzinfo)
    if local_dt.year == local_now.year:
        return local_dt.strftime("%b %d")
    return local_dt.strftime("%b %d, %Y")


templates.env.filters["friendly_time"] = friendly_time


def _serialize_requests(db: Session, items, viewer: Optional[User] = None):
    creator_usernames = request_services.load_creator_usernames(db, items)
    serialized = []
    for item in items:
        can_complete = calculate_can_complete(item, viewer) if viewer else False
        serialized.append(
            RequestResponse.from_model(
                item,
                created_by_username=creator_usernames.get(item.created_by_user_id),
                can_complete=can_complete,
            ).model_dump()
        )
    return serialized


def describe_session_role(user: User, session: Optional[UserSession]) -> Optional[dict[str, str]]:
    if not session:
        return None

    if not session.is_fully_authenticated:
        label = "Admin (pending verification)" if user.is_admin else "Pending verification"
        return {"label": label, "tone": "warning"}

    if user.is_admin:
        return {"label": "Administrator", "tone": "accent"}

    return {"label": "Member", "tone": "muted"}




@router.get("/login")
def login_form(
    request: Request,
    session_record: Optional[UserSession] = Depends(get_current_session),
):
    if session_record and session_record.is_fully_authenticated:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
def login_submit(
    request: Request,
    db: SessionDep,
    response: Response,
    *,
    username: Annotated[str, Form(...)],
) -> Response:
    normalized = auth_service.normalize_username(username)
    user = db.exec(select(User).where(User.username == normalized)).first()
    if not user:
        context = {"request": request, "error": "Username not found.", "username": username}
        return templates.TemplateResponse("auth/login.html", context, status_code=status.HTTP_200_OK)

    auth_request, session_record = auth_service.create_auth_request(
        db,
        user=user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    apply_session_cookie(response, session_record)

    context = {
        "request": request,
        "verification_code": auth_request.verification_code,
        "username": user.username,
        "error": None,
    }
    template_response = templates.TemplateResponse("auth/login_pending.html", context)
    apply_session_cookie(template_response, session_record)
    return template_response

@router.post("/login/verify")
def verify_login(
    request: Request,
    db: SessionDep,
    *,
    username: Annotated[str, Form(...)],
    verification_code: Annotated[str, Form(...)],
) -> Response:
    try:
        auth_request = auth_service.find_pending_auth_request(
            db,
            username=username,
            verification_code=verification_code,
        )
    except HTTPException as exc:
        context = {
            "request": request,
            "username": username,
            "verification_code": verification_code,
            "error": exc.detail,
        }
        return templates.TemplateResponse("auth/login_pending.html", context, status_code=exc.status_code)

    auth_service.approve_auth_request(db, auth_request=auth_request, approver=None)

    session_record = db.exec(
        select(UserSession).where(UserSession.auth_request_id == auth_request.id)
    ).first()
    if not session_record:
        context = {
            "request": request,
            "username": username,
            "verification_code": auth_request.verification_code,
            "error": "Session missing. Request access again.",
        }
        return templates.TemplateResponse("auth/login_pending.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    apply_session_cookie(redirect_response, session_record)
    return redirect_response

@router.get("/register")
def register_form(request: Request, db: SessionDep) -> Response:
    prefilled_token = request.query_params.get("invite_token")
    suggested_username = ""
    suggested_bio = ""
    invite_personalization = None

    if prefilled_token:
        invite_record = db.get(InviteToken, prefilled_token)
        if invite_record:
            suggested_username = invite_record.suggested_username or ""
            suggested_bio = invite_record.suggested_bio or ""
            personalization_record = auth_service.get_invite_personalization(db, invite_record.token)
            personalization_data = auth_service.serialize_invite_personalization(personalization_record)
            if personalization_data:
                personalization_data["suggested_username"] = suggested_username
                invite_personalization = personalization_data

    context = {
        "request": request,
        "prefilled_invite_token": prefilled_token or "",
        "suggested_username": suggested_username,
        "suggested_bio": suggested_bio,
        "invite_personalization": invite_personalization,
    }
    return templates.TemplateResponse("auth/register.html", context)


@router.post("/register")
def register_submit(
    request: Request,
    db: SessionDep,
    *,
    username: Annotated[str, Form(...)],
    invite_token: Annotated[Optional[str], Form()] = None,
    contact_email: Annotated[Optional[str], Form()] = None,
    initial_request: Annotated[Optional[str], Form()] = None,
):
    try:
        registration = auth_service.create_user_with_invite(
            db,
            username=username,
            contact_email=contact_email,
            invite_token=invite_token,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST and str(exc.detail) == "Invite token required":
            context = {"request": request, "username": username}
            return templates.TemplateResponse("auth/invite_required.html", context, status_code=exc.status_code)
        raise

    created_request = False
    if initial_request and initial_request.strip():
        request_services.create_request(
            db,
            user=registration.user,
            description=initial_request,
            contact_email=contact_email,
        )
        created_request = True

    if registration.session:
        redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        apply_session_cookie(redirect, registration.session)
        return redirect

    context = {
        "request": request,
        "username": registration.user.username,
        "created_request": created_request,
    }
    return templates.TemplateResponse("auth/register_success.html", context)




@router.post("/logout")
def logout_user(
    db: SessionDep,
    session_record: Optional[UserSession] = Depends(get_current_session),
):
    if session_record:
        auth_service.revoke_session(db, session_id=session_record.id)
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(auth_service.SESSION_COOKIE_NAME, path="/")
    return response

@router.get("/")
def home(
    request: Request,
    db: SessionDep,
    session_record: Optional[UserSession] = Depends(get_current_session),
) -> Response:
    if not session_record:
        return templates.TemplateResponse("auth/logged_out.html", {"request": request})

    user = db.exec(select(User).where(User.id == session_record.user_id)).first()
    if not user:
        response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(auth_service.SESSION_COOKIE_NAME, path="/")
        return response

    session_role = describe_session_role(user, session_record)

    if not session_record.is_fully_authenticated:
        auth_request = None
        if session_record.auth_request_id:
            auth_request = db.exec(
                select(AuthenticationRequest).where(AuthenticationRequest.id == session_record.auth_request_id)
            ).first()

        public_requests = _serialize_requests(db, request_services.list_requests(db), viewer=user)
        pending_requests = _serialize_requests(
            db,
            request_services.list_pending_requests_for_user(db, user_id=user.id),
            viewer=user,
        )

        session_avatar_url = _get_account_avatar(db, user.id)

        context = {
            "request": request,
            "user": user,
            "requests": public_requests,
            "pending_requests": pending_requests,
            "verification_code": auth_request.verification_code if auth_request else None,
            "auth_request": auth_request,
            "readonly": True,
            "session": session_record,
            "session_role": session_role,
            "session_username": user.username,
            "session_avatar_url": session_avatar_url,
        }
        return templates.TemplateResponse("requests/pending.html", context)

    session_avatar_url = _get_account_avatar(db, user.id)
    public_requests = _serialize_requests(db, request_services.list_requests(db), viewer=user)
    return templates.TemplateResponse(
        "requests/index.html",
        {
            "request": request,
            "user": user,
            "requests": public_requests,
            "readonly": False,
            "session": session_record,
            "session_role": session_role,
            "session_username": user.username,
            "session_avatar_url": session_avatar_url,
        },
    )


@router.get("/requests/{request_id}")
def request_detail(
    request: Request,
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    viewer = session_user.user
    session_record = session_user.session

    help_request = request_services.get_request_by_id(db, request_id=request_id)

    if help_request.status == "pending" and not (
        viewer.is_admin or help_request.created_by_user_id == viewer.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    creator_usernames = request_services.load_creator_usernames(db, [help_request])
    serialized = RequestResponse.from_model(
        help_request,
        created_by_username=creator_usernames.get(help_request.created_by_user_id),
        can_complete=calculate_can_complete(help_request, viewer),
    )

    readonly = not session_record.is_fully_authenticated
    session_role = describe_session_role(viewer, session_record)

    context = {
        "request": request,
        "user": viewer,
        "readonly": readonly,
        "request_item": serialized,
        "session": session_record,
        "session_role": session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
    }

    return templates.TemplateResponse("requests/detail.html", context)


@router.get("/invite/new")
def invite_new(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    context = {
        "request": request,
        "inviter_username": session_user.user.username,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "session_avatar_url": session_user.avatar_url,
    }
    return templates.TemplateResponse("invite/new.html", context)


CONTACT_EMAIL_MAX_LENGTH = 255
PROFILE_PHOTO_MAX_BYTES = 5 * 1024 * 1024
PROFILE_PHOTO_DIR = Path("static/uploads/profile_photos")
PROFILE_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
PROFILE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

PROFILE_PHOTO_DIR.mkdir(parents=True, exist_ok=True)


def _build_account_settings_context(
    request: Request,
    db: Session,
    session_user: SessionUser,
    *,
    form_values: Optional[dict[str, Optional[str]]] = None,
    form_message: Optional[str] = None,
    form_status: Optional[str] = None,
    form_errors: Optional[list[str]] = None,
) -> dict[str, object]:
    user = session_user.user
    session_record = session_user.session
    session_avatar_url = _get_account_avatar(db, user.id)
    session_role = describe_session_role(user, session_record)

    if form_values is None:
        form_values = {
            "contact_email": user.contact_email or "",
        }

    return {
        "request": request,
        "user": user,
        "session": session_record,
        "session_role": session_role,
        "session_username": user.username,
        "session_avatar_url": session_avatar_url,
        "form_values": form_values,
        "form_message": form_message,
        "form_status": form_status,
        "form_errors": form_errors or [],
        "current_avatar_url": session_avatar_url,
    }


def _validate_contact_email(value: str) -> Optional[str]:
    if not value:
        return None
    if len(value) > CONTACT_EMAIL_MAX_LENGTH:
        return "Contact email must be 255 characters or fewer."
    if "@" not in value or value.count("@") != 1:
        return "Enter a valid email address."
    local_part, domain_part = value.split("@", 1)
    if not local_part or not domain_part or "." not in domain_part:
        return "Enter a valid email address."
    return None


async def _store_profile_photo(upload: UploadFile) -> str:
    if not upload or not upload.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Select a photo to upload.")

    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded photo is empty.")
    if len(contents) > PROFILE_PHOTO_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Photo must be 5 MB or smaller.",
        )

    content_type = upload.content_type or ""
    if content_type not in PROFILE_ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Use JPEG, PNG, or WebP images.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in PROFILE_ALLOWED_EXTENSIONS:
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(content_type, ".png")

    filename = f"{uuid4().hex}{suffix}"
    destination = PROFILE_PHOTO_DIR / filename
    destination.write_bytes(contents)
    return f"/static/uploads/profile_photos/{filename}"


@router.get("/settings/account")
def account_settings(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    context = _build_account_settings_context(request, db, session_user)
    return templates.TemplateResponse("settings/account.html", context)


@router.post("/settings/account")
async def account_settings_submit(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    contact_email: Annotated[Optional[str], Form()] = None,
    profile_photo: Annotated[Optional[UploadFile], File()] = None,
    remove_photo: Annotated[Optional[str], Form()] = None,
) -> Response:
    normalized_email = (contact_email or "").strip()
    form_values = {"contact_email": normalized_email}
    errors: list[str] = []

    validation_error = _validate_contact_email(normalized_email)
    if validation_error:
        errors.append(validation_error)

    new_avatar_url: Optional[str] = None
    remove_photo_requested = bool(remove_photo)

    if profile_photo and profile_photo.filename:
        try:
            new_avatar_url = await _store_profile_photo(profile_photo)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Unable to upload photo."
            errors.append(detail)

    if errors:
        context = _build_account_settings_context(
            request,
            db,
            session_user,
            form_values=form_values,
            form_errors=errors,
            form_status="error",
        )
        return templates.TemplateResponse("settings/account.html", context)

    user = session_user.user
    user.contact_email = normalized_email or None
    db.add(user)

    if remove_photo_requested:
        user_attribute_service.delete_attribute(
            db,
            user_id=user.id,
            key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
        )
    elif new_avatar_url:
        user_attribute_service.set_attribute(
            db,
            user_id=user.id,
            key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
            value=new_avatar_url,
            actor_user_id=user.id,
        )

    db.commit()
    db.refresh(user)

    context = _build_account_settings_context(
        request,
        db,
        session_user,
        form_values={"contact_email": user.contact_email or ""},
        form_message="Account details updated.",
        form_status="success",
    )
    return templates.TemplateResponse("settings/account.html", context)


@router.get("/invite/map")
def invite_map(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    user = session_user.user
    invite_map = invite_map_cache_service.get_cached_map(db, user_id=user.id)
    cache_hit = invite_map is not None
    if not invite_map:
        invite_map = invite_graph_service.build_bidirectional_invite_map(
            db,
            root_user_id=user.id,
            max_degree=invite_graph_service.DEFAULT_MAP_DEGREE,
        )
        if invite_map:
            invite_map_cache_service.store_cached_map(db, user_id=user.id, invite_map=invite_map)

    context = {
        "request": request,
        "session": session_user.session,
        "session_role": describe_session_role(user, session_user.session),
        "session_username": user.username,
        "user": user,
        "invite_map": invite_map,
        "invite_map_cache_hit": cache_hit,
    }
    return templates.TemplateResponse("invite/map.html", context)


@router.get("/profile")
def profile(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    user = session_user.user
    session_record = session_user.session
    is_half_authenticated = not session_record.is_fully_authenticated
    session_role = describe_session_role(user, session_record)

    privilege_descriptors = [
        {
            "key": "member",
            "label": "Standard member",
            "active": True,
            "description": "Can browse community requests and submit new ones once their session is fully verified.",
        },
        {
            "key": "admin",
            "label": "Administrator",
            "active": user.is_admin,
            "description": (
                "Can approve access, manage invites, and moderate requests."
                if user.is_admin
                else "Reserved for administrators who can approve access, manage invites, and moderate requests."
            ),
        },
        {
            "key": "half_auth",
            "label": "Half-authenticated session",
            "active": is_half_authenticated,
            "description": (
                "Verify your login to unlock full access to posting and moderation tools."
                if is_half_authenticated
                else "This session is fully verified; no additional login steps are required."
            ),
        },
    ]

    session_avatar_url = session_user.avatar_url
    active_privileges = [descriptor for descriptor in privilege_descriptors if descriptor["active"]]

    context = {
        "request": request,
        "user": user,
        "session": session_record,
        "session_role": session_role,
        "session_username": user.username,
        "identity": {
            "username": user.username,
            "contact_email": user.contact_email,
            "created_at": user.created_at,
            "avatar_url": session_avatar_url,
        },
        "privileges": active_privileges,
        "is_admin": user.is_admin,
        "is_half_authenticated": is_half_authenticated,
        "session_avatar_url": session_avatar_url,
    }
    return templates.TemplateResponse("profile/index.html", context)


@router.get("/people/{username}")
def profile_view(
    username: str,
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    normalized = auth_service.normalize_username(username)
    person = db.exec(select(User).where(User.username == normalized)).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    viewer = session_user.user
    is_self = viewer.id == person.id
    can_view_contact = viewer.is_admin or is_self
    viewer_session = session_user.session
    viewer_session_role = describe_session_role(viewer, viewer_session)

    avatar_url = user_attribute_service.get_attribute(
        db,
        user_id=person.id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )

    identity = {
        "username": person.username,
        "contact_email": person.contact_email if can_view_contact else None,
        "created_at": person.created_at,
        "avatar_url": avatar_url,
    }

    context = {
        "request": request,
        "viewer": viewer,
        "person": person,
        "identity": identity,
        "is_self": is_self,
        "can_view_contact": can_view_contact,
        "contact_restricted": bool(person.contact_email and not can_view_contact),
        "user": viewer,
        "session": viewer_session,
        "session_role": viewer_session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
    }
    return templates.TemplateResponse("profile/show.html", context)


@router.post("/requests")
def create_request(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    *,
    description: Annotated[str, Form()],
    contact_email: Annotated[Optional[str], Form()] = None,
):
    status_value = "open" if session_user.session.is_fully_authenticated else "pending"
    request_services.create_request(
        db,
        user=session_user.user,
        description=description,
        contact_email=contact_email,
        status_value=status_value,
    )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    request: Request,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
):
    request_services.mark_completed(db, request_id=request_id, user=user)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
def _get_account_avatar(db: Session, user_id: int) -> Optional[str]:
    return user_attribute_service.get_attribute(
        db,
        user_id=user_id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )
