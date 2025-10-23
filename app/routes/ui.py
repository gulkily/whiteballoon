from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.dependencies import (
    SessionDep,
    SessionUser,
    apply_session_cookie,
    get_current_session,
    require_authenticated_user,
    require_session_user,
)
from app.models import AuthenticationRequest, User, UserSession
from app.modules.requests import services as request_services
from app.modules.requests.routes import RequestResponse
from app.services import auth_service

router = APIRouter(tags=["ui"])

templates = Jinja2Templates(directory="templates")


def _serialize_requests(items):
    return [RequestResponse.from_model(item).model_dump() for item in items]




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
def register_form(request: Request) -> Response:
    return templates.TemplateResponse("auth/register.html", {"request": request})


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
    user = auth_service.create_user_with_invite(
        db,
        username=username,
        contact_email=contact_email,
        invite_token=invite_token,
    )

    created_request = False
    if initial_request and initial_request.strip():
        request_services.create_request(
            db,
            user=user,
            description=initial_request,
            contact_email=contact_email,
        )
        created_request = True

    context = {"request": request, "username": user.username, "created_request": created_request}
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

    if not session_record.is_fully_authenticated:
        auth_request = None
        if session_record.auth_request_id:
            auth_request = db.exec(
                select(AuthenticationRequest).where(AuthenticationRequest.id == session_record.auth_request_id)
            ).first()

        public_requests = _serialize_requests(request_services.list_requests(db))
        pending_requests = [
            RequestResponse.from_model(item).model_dump()
            for item in request_services.list_pending_requests_for_user(db, user_id=user.id)
        ]

        context = {
            "request": request,
            "user": user,
            "requests": public_requests,
            "pending_requests": pending_requests,
            "verification_code": auth_request.verification_code if auth_request else None,
            "auth_request": auth_request,
            "readonly": True,
        }
        return templates.TemplateResponse("requests/pending.html", context)

    public_requests = _serialize_requests(request_services.list_requests(db))
    return templates.TemplateResponse(
        "requests/index.html",
        {"request": request, "user": user, "requests": public_requests, "readonly": False},
    )


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
