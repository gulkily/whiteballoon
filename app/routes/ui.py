from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.dependencies import (
    SessionDep,
    apply_session_cookie,
    get_current_session,
    require_authenticated_user,
)
from app.models import User, UserSession
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
):
    normalized = auth_service.normalize_username(username)
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

    context = {
        "request": request,
        "verification_code": auth_request.verification_code,
        "username": user.username,
    }
    return templates.TemplateResponse("auth/login_pending.html", context)


@router.post("/login/verify")
def verify_login(
    request: Request,
    db: SessionDep,
    response: Response,
    *,
    username: Annotated[str, Form(...)],
    verification_code: Annotated[str, Form(...)],
):
    auth_request = auth_service.find_pending_auth_request(
        db,
        username=username,
        verification_code=verification_code,
    )

    auth_service.approve_auth_request(db, auth_request=auth_request, approver=None)

    session_record = db.exec(
        select(UserSession).where(UserSession.auth_request_id == auth_request.id)
    ).first()
    if not session_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session missing")

    apply_session_cookie(response, session_record)

    if request.headers.get("HX-Request") == "true":
        response.headers["HX-Redirect"] = "/"
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/register")
def register_form(request: Request) -> Response:
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
def register_submit(
    request: Request,
    db: SessionDep,
    *,
    username: Annotated[str, Form(...)],
    display_name: Annotated[Optional[str], Form()] = None,
    invite_token: Annotated[Optional[str], Form()] = None,
    contact_email: Annotated[Optional[str], Form()] = None,
):
    user = auth_service.create_user_with_invite(
        db,
        username=username,
        display_name=display_name,
        contact_email=contact_email,
        invite_token=invite_token,
    )

    context = {"request": request, "username": user.username, "display_name": user.display_name}
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
    user: User = Depends(require_authenticated_user),
) -> Response:
    items = _serialize_requests(request_services.list_requests(db))
    return templates.TemplateResponse(
        "requests/index.html",
        {"request": request, "user": user, "requests": items},
    )


@router.get("/requests/partials/list")
def request_list_partial(
    request: Request,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
):
    items = _serialize_requests(request_services.list_requests(db))
    return templates.TemplateResponse(
        "requests/partials/list.html",
        {"request": request, "requests": items, "user": user},
    )


@router.post("/requests")
def create_request(
    request: Request,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
    *,
    title: Annotated[str, Form(...)],
    description: Annotated[str, Form()] = "",
    contact_email: Annotated[Optional[str], Form()] = None,
):
    request_services.create_request(
        db,
        user=user,
        title=title,
        description=description,
        contact_email=contact_email,
    )
    items = _serialize_requests(request_services.list_requests(db))
    context = {"request": request, "requests": items, "user": user}

    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse("requests/partials/list.html", context)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    request: Request,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
):
    request_services.mark_completed(db, request_id=request_id, user=user)
    items = _serialize_requests(request_services.list_requests(db))
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "requests/partials/list.html",
            {"request": request, "requests": items, "user": user},
        )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
