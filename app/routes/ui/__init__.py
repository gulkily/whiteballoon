from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Optional
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
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import Session, select

from app.dependencies import (
    SessionDep,
    SessionUser,
    get_current_session,
    require_authenticated_user,
    require_session_user,
)
from app.models import AuthenticationRequest, HelpRequest, RequestComment, User, UserSession
from app.modules.requests import services as request_services
from app.modules.requests.routes import RequestResponse, calculate_can_complete
from app.services import (
    auth_service,
    invite_graph_service,
    invite_map_cache_service,
    request_comment_service,
    user_attribute_service,
    vouch_service,
)
from app.url_utils import build_invite_link, generate_qr_code_data_url
from .helpers import describe_session_role, templates

router = APIRouter(tags=["ui"])

logger = logging.getLogger(__name__)


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
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    context = _build_request_detail_context(request, db, session_user, help_request)
    return templates.TemplateResponse("requests/detail.html", context)


@router.post("/requests/{request_id}/comments")
async def create_request_comment(
    request: Request,
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    body: Annotated[Optional[str], Form()] = None,
) -> Response:
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    viewer = session_user.user
    session_record = session_user.session

    if not session_record.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fully authenticated session required")

    trimmed_body = (body or "").strip()
    errors: list[str] = []

    try:
        comment = request_comment_service.add_comment(
            db,
            help_request_id=help_request.id,
            user_id=viewer.id,
            body=trimmed_body,
        )
    except ValueError as exc:
        errors.append(str(exc))
        comment = None

    wants_json = _wants_json(request)

    if errors:
        if wants_json:
            return JSONResponse({"errors": errors}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        context = _build_request_detail_context(
            request,
            db,
            session_user,
            help_request,
            comment_form_errors=errors,
            comment_form_body=trimmed_body,
        )
        return templates.TemplateResponse(
            "requests/detail.html",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    db.commit()
    db.refresh(comment)

    comment_payload = request_comment_service.serialize_comment(comment, viewer)
    fragment = templates.get_template("requests/partials/comment.html").render(
        {
            "request": request,
            "comment": comment_payload,
            "can_moderate_comments": viewer.is_admin,
            "can_toggle_sync_scope": viewer.is_admin,
            "request_id": help_request.id,
        }
    )

    if wants_json:
        return JSONResponse({"html": fragment, "comment": comment_payload})

    return RedirectResponse(url=f"/requests/{request_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/comments/{comment_id}/delete")
def delete_request_comment(
    request: Request,
    request_id: int,
    comment_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    viewer = session_user.user

    if not viewer.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    comment = db.get(RequestComment, comment_id)
    if not comment or comment.help_request_id != help_request.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    request_comment_service.soft_delete_comment(db, comment_id)
    db.commit()

    if _wants_json(request):
        return JSONResponse({"deleted": True, "comment_id": comment_id})

    return RedirectResponse(url=f"/requests/{request_id}", status_code=status.HTTP_303_SEE_OTHER)


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


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    if "application/json" in accept:
        return True
    requested_with = request.headers.get("x-requested-with", "")
    return requested_with.lower() in {"fetch", "xmlhttprequest"}



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


def _build_request_detail_context(
    request: Request,
    db: Session,
    session_user: SessionUser,
    help_request: HelpRequest,
    *,
    comment_form_errors: Optional[list[str]] = None,
    comment_form_body: str = "",
) -> dict[str, object]:
    viewer = session_user.user
    session_record = session_user.session

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

    comment_rows = request_comment_service.list_comments(db, help_request_id=help_request.id)
    comments = [request_comment_service.serialize_comment(comment, author) for comment, author in comment_rows]
    can_moderate = viewer.is_admin
    can_toggle_sync_scope = viewer.is_admin

    return {
        "request": request,
        "user": viewer,
        "readonly": readonly,
        "request_item": serialized,
        "session": session_record,
        "session_role": session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "comments": comments,
        "can_comment": session_record.is_fully_authenticated,
        "can_moderate_comments": can_moderate,
        "can_toggle_sync_scope": can_toggle_sync_scope,
        "comment_form_errors": comment_form_errors or [],
        "comment_form_body": comment_form_body,
        "comment_max_length": request_comment_service.MAX_COMMENT_LENGTH,
        "request_id": help_request.id,
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


from . import sessions as session_routes
from . import sync as sync_routes


router.include_router(session_routes.router)
router.include_router(sync_routes.router)
