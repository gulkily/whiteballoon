from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.dependencies import SessionDep, SessionUser, require_authenticated_user, require_session_user
from app.models import HelpRequest, User
from app.modules.requests import services

router = APIRouter(prefix="/api/requests", tags=["requests"])


class RequestCreatePayload(BaseModel):
    description: str
    contact_email: str | None = None


class RequestResponse(BaseModel):
    id: int
    description: str
    status: str
    contact_email: str | None
    created_by_user_id: int | None
    created_by_username: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None
    can_complete: bool = False
    sync_scope: str = "private"

    @classmethod
    def from_model(
        cls,
        request: HelpRequest,
        *,
        created_by_username: str | None = None,
        can_complete: bool = False,
    ) -> "RequestResponse":
        return cls(
            id=request.id,
            description=request.description,
            status=request.status,
            contact_email=request.contact_email,
            created_by_user_id=request.created_by_user_id,
            created_by_username=created_by_username,
            created_at=request.created_at.isoformat() + "Z",
            updated_at=request.updated_at.isoformat() + "Z",
            completed_at=request.completed_at.isoformat() + "Z" if request.completed_at else None,
            can_complete=can_complete,
            sync_scope=getattr(request, "sync_scope", "private"),
        )


def calculate_can_complete(help_request: HelpRequest, user: User) -> bool:
    if help_request.status != "open":
        return False
    if user.is_admin:
        return True
    return help_request.created_by_user_id == user.id


@router.get("/", response_model=List[RequestResponse])
def list_requests(db: SessionDep, session_user: SessionUser = Depends(require_session_user)) -> List[RequestResponse]:
    requests = services.list_requests(db)
    creator_usernames = services.load_creator_usernames(db, requests)
    return [
        RequestResponse.from_model(
            item,
            created_by_username=creator_usernames.get(item.created_by_user_id),
            can_complete=calculate_can_complete(item, session_user.user),
        )
        for item in requests
    ]


@router.get("/pending", response_model=List[RequestResponse])
def list_pending_requests(db: SessionDep, session_user: SessionUser = Depends(require_session_user)) -> List[RequestResponse]:
    pending_requests = services.list_pending_requests_for_user(db, user_id=session_user.user.id)
    creator_usernames = services.load_creator_usernames(db, pending_requests)
    return [
        RequestResponse.from_model(
            item,
            created_by_username=creator_usernames.get(item.created_by_user_id),
            can_complete=calculate_can_complete(item, session_user.user),
        )
        for item in pending_requests
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
def create_request(
    payload: RequestCreatePayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> RequestResponse:
    status_value = "open" if session_user.session.is_fully_authenticated else "pending"
    help_request = services.create_request(
        db,
        user=session_user.user,
        description=payload.description,
        contact_email=payload.contact_email,
        status_value=status_value,
    )
    return RequestResponse.from_model(
        help_request,
        created_by_username=session_user.user.username,
        can_complete=calculate_can_complete(help_request, session_user.user),
    )


@router.post("/{request_id}/complete", response_model=RequestResponse)
def complete_request(
    request_id: int,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
) -> RequestResponse:
    help_request = services.mark_completed(db, request_id=request_id, user=user)
    # Completed requests should not expose the completion action.
    creator_usernames = services.load_creator_usernames(db, [help_request])
    return RequestResponse.from_model(
        help_request,
        created_by_username=creator_usernames.get(help_request.created_by_user_id),
        can_complete=False,
    )
