from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session

from app.dependencies import SessionDep, require_authenticated_user
from app.models import HelpRequest, User
from app.modules.requests import services

router = APIRouter(prefix="/requests", tags=["requests"])


class RequestCreatePayload(BaseModel):
    title: str
    description: str = ""
    contact_email: str | None = None


class RequestResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    contact_email: str | None
    created_at: str
    updated_at: str
    completed_at: str | None

    @classmethod
    def from_model(cls, request: HelpRequest) -> "RequestResponse":
        return cls(
            id=request.id,
            title=request.title,
            description=request.description,
            status=request.status,
            contact_email=request.contact_email,
            created_at=request.created_at.isoformat() + "Z",
            updated_at=request.updated_at.isoformat() + "Z",
            completed_at=request.completed_at.isoformat() + "Z" if request.completed_at else None,
        )


@router.get("/", response_model=List[RequestResponse])
def list_requests(db: SessionDep, user: User = Depends(require_authenticated_user)) -> List[RequestResponse]:
    requests = services.list_requests(db)
    return [RequestResponse.from_model(item) for item in requests]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RequestResponse)
def create_request(
    payload: RequestCreatePayload,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
) -> RequestResponse:
    help_request = services.create_request(
        db,
        user=user,
        title=payload.title,
        description=payload.description,
        contact_email=payload.contact_email,
    )
    return RequestResponse.from_model(help_request)


@router.post("/{request_id}/complete", response_model=RequestResponse)
def complete_request(
    request_id: int,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
) -> RequestResponse:
    help_request = services.mark_completed(db, request_id=request_id, user=user)
    return RequestResponse.from_model(help_request)
