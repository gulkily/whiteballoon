from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel

from app.dependencies import SessionDep, SessionUser, require_authenticated_user, require_session_user
from app.models import HelpRequest, User
from app.modules.requests import services
from app.services import (
    recurring_template_service,
    request_channel_metrics,
    request_channel_reads,
    request_pin_service,
)

router = APIRouter(prefix="/api/requests", tags=["requests"])


class RequestCreatePayload(BaseModel):
    description: str
    contact_email: str | None = None


class DraftSavePayload(BaseModel):
    id: int | None = None
    description: str | None = None
    contact_email: str | None = None


class PublishDraftPayload(BaseModel):
    description: str | None = None
    contact_email: str | None = None


class RequestResponse(BaseModel):
    id: int
    description: str
    status: str
    contact_email: str | None
    created_by_user_id: int | None
    created_by_username: str | None = None
    created_by_display_name: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None
    can_complete: bool = False
    sync_scope: str = "private"
    is_pinned: bool = False
    pin_rank: int | None = None
    comment_count: int | None = None
    unread_count: int | None = None
    recurring_template_id: int | None = None
    recurring_template_title: str | None = None

    @classmethod
    def from_model(
        cls,
        request: HelpRequest,
        *,
        created_by_username: str | None = None,
        created_by_display_name: str | None = None,
        can_complete: bool = False,
        is_pinned: bool = False,
        pin_rank: int | None = None,
        comment_count: int | None = None,
        unread_count: int | None = None,
        recurring_template_id: int | None = None,
        recurring_template_title: str | None = None,
    ) -> "RequestResponse":
        return cls(
            id=request.id,
            description=request.description,
            status=request.status,
            contact_email=request.contact_email,
            created_by_user_id=request.created_by_user_id,
            created_by_username=created_by_username,
            created_by_display_name=created_by_display_name,
            created_at=request.created_at.isoformat() + "Z",
            updated_at=request.updated_at.isoformat() + "Z",
            completed_at=request.completed_at.isoformat() + "Z" if request.completed_at else None,
            can_complete=can_complete,
            sync_scope=getattr(request, "sync_scope", "private"),
            is_pinned=is_pinned,
            pin_rank=pin_rank,
            comment_count=comment_count,
            unread_count=unread_count,
            recurring_template_id=recurring_template_id,
            recurring_template_title=recurring_template_title,
        )


def calculate_can_complete(help_request: HelpRequest, user: User) -> bool:
    if help_request.status != "open":
        return False
    if user.is_admin:
        return True
    return help_request.created_by_user_id == user.id


@router.get("/", response_model=List[RequestResponse])
def list_requests(
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    search: str | None = Query(None),
    status: list[str] | None = Query(None),
    pinned_only: bool = Query(False, alias="pinned_only"),
    limit: int | None = Query(50, ge=1, le=200),
    include_channel_meta: bool = Query(False, alias="include_channel_meta"),
) -> List[RequestResponse]:
    requests = services.list_requests(
        db,
        search=search,
        statuses=status,
        pinned_only=pinned_only,
        limit=limit,
    )
    creator_usernames = services.load_creator_usernames(db, requests)
    pin_map = request_pin_service.get_pin_map(db)
    template_metadata = recurring_template_service.load_template_metadata(
        db,
        [item.id for item in requests if item.id],
    )
    comment_counts: dict[int, int] = {}
    unread_totals: dict[int, int] = {}
    if include_channel_meta:
        request_ids = [item.id for item in requests if item.id]
        session_record = session_user.session
        last_seen = getattr(session_record, "last_seen_at", None)
        comment_counts, recent_counts = request_channel_metrics.load_comment_counts(
            db,
            request_ids,
            newer_than=last_seen,
        )
        read_counts = {}
        session_id = getattr(session_record, "id", None)
        if session_id:
            read_counts = request_channel_reads.get_read_counts(session_id, request_ids)
        for request_id in request_ids:
            unread = recent_counts.get(request_id, 0)
            if request_id in read_counts:
                unread = max(comment_counts.get(request_id, 0) - read_counts[request_id], 0)
            unread_totals[request_id] = unread
    return [
        RequestResponse.from_model(
            item,
            created_by_username=creator_usernames.get(item.created_by_user_id),
            can_complete=calculate_can_complete(item, session_user.user),
            is_pinned=item.id in pin_map,
            pin_rank=pin_map.get(item.id).rank if item.id in pin_map else None,
            comment_count=comment_counts.get(item.id),
            unread_count=unread_totals.get(item.id),
            recurring_template_id=template_metadata.get(item.id, {}).get("template_id") if template_metadata else None,
            recurring_template_title=template_metadata.get(item.id, {}).get("template_title") if template_metadata else None,
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


@router.get("/drafts", response_model=List[RequestResponse])
def list_drafts(
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> List[RequestResponse]:
    drafts = services.list_drafts_for_user(db, user_id=session_user.user.id)
    return [
        RequestResponse.from_model(
            draft,
            created_by_username=session_user.user.username,
        )
        for draft in drafts
    ]


@router.post("/drafts", response_model=RequestResponse)
def save_draft(
    payload: DraftSavePayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> RequestResponse:
    draft = services.save_draft(
        db,
        user=session_user.user,
        description=payload.description,
        contact_email=payload.contact_email,
        draft_id=payload.id,
    )
    return RequestResponse.from_model(
        draft,
        created_by_username=session_user.user.username,
    )


@router.post("/{request_id}/publish", response_model=RequestResponse)
def publish_request(
    request_id: int,
    payload: PublishDraftPayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> RequestResponse:
    help_request = services.publish_draft(
        db,
        draft_id=request_id,
        user=session_user.user,
        is_fully_authenticated=session_user.session.is_fully_authenticated,
        description=payload.description,
        contact_email=payload.contact_email,
    )
    return RequestResponse.from_model(
        help_request,
        created_by_username=session_user.user.username,
        can_complete=calculate_can_complete(help_request, session_user.user),
    )


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    services.delete_draft(db, draft_id=request_id, user=session_user.user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
