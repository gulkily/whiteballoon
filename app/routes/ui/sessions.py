from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from app.dependencies import SessionDep, apply_session_cookie, get_current_session
from app.models import InviteToken, User, UserSession
from app.routes.ui.helpers import templates
from app.modules.requests import services as request_services
from app.services import auth_service

router = APIRouter(tags=["ui"])


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
        return templates.TemplateResponse(
            "auth/login_pending.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    apply_session_cookie(redirect_response, session_record)
    return redirect_response


@router.get("/register")
@router.get("/register/{invite_token}")
def register_form(request: Request, db: SessionDep, invite_token: Optional[str] = None) -> Response:
    prefilled_token = invite_token or request.query_params.get("invite_token")
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


__all__ = ["router"]
