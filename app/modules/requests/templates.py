from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_session, require_authenticated_user, SessionDep
from app.models import User, UserSession

from . import services
from .routes import RequestResponse

router = APIRouter(prefix="/requests/partials", tags=["requests-partials"])
templates = Jinja2Templates(directory="templates")


def _serialize_requests(db: SessionDep) -> list[RequestResponse]:
    items = services.list_requests(db)
    return [RequestResponse.from_model(item) for item in items]


@router.get("/form/show")
def show_form(
    db: SessionDep,
    session_record: Optional[UserSession] = Depends(get_current_session),
):
    if not session_record or not session_record.is_fully_authenticated:
        return templates.TemplateResponse(
            "auth/login_required_fragment.html",
            {"message": "Sign in to share a request."},
        )

    user = db.get(User, session_record.user_id)
    if not user:
        return templates.TemplateResponse(
            "auth/login_required_fragment.html",
            {"message": "Session invalid. Please sign in again."},
        )

    context = {"user": user}
    return templates.TemplateResponse("requests/partials/form.html", context)


@router.get("/form/cancel")
def cancel_form():
    return templates.TemplateResponse("requests/partials/form_closed.html", {})


@router.get("/list")
def list_partial(db: SessionDep, user: User = Depends(require_authenticated_user)):
    responses = _serialize_requests(db)
    return templates.TemplateResponse(
        "requests/partials/list.html",
        {"requests": responses, "user": user},
    )
