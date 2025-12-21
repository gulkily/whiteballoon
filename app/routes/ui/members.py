from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from starlette.datastructures import URL

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates
from app.services import member_directory_service, user_attribute_service

router = APIRouter(tags=["ui"])


@router.get("/members")
def members_directory(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    page: int = Query(1, ge=1),
    q: Optional[str] = Query(None, alias="username"),
    contact: Optional[str] = None,
):
    session_record = session_user.session
    if not session_record.is_fully_authenticated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full membership required")

    filters = member_directory_service.MemberDirectoryFilters(
        username=q,
        contact=contact,
    )
    directory_page = member_directory_service.list_members(
        db,
        viewer=session_user.user,
        page=page,
        filters=filters,
    )

    member_ids = [profile.id for profile in directory_page.profiles if profile.id is not None]
    avatar_urls = user_attribute_service.load_profile_photo_urls(
        db,
        user_ids=member_ids,
    )
    display_names = user_attribute_service.load_display_names(
        db,
        user_ids=member_ids,
    )

    def _page_url(target_page: int) -> str:
        url: URL = request.url.include_query_params(page=target_page)
        return str(url)

    pagination = {
        "has_prev": directory_page.page > 1,
        "has_next": directory_page.page < directory_page.total_pages,
        "prev_url": _page_url(directory_page.page - 1) if directory_page.page > 1 else None,
        "next_url": _page_url(directory_page.page + 1)
        if directory_page.page < directory_page.total_pages
        else None,
    }

    context = {
        "request": request,
        "user": session_user.user,
        "session": session_record,
        "session_role": describe_session_role(session_user.user, session_record),
        "session_username": session_user.user.username,
        "session_avatar_url": session_user.avatar_url,
        "profiles": directory_page.profiles,
        "profiles_total": directory_page.total_count,
        "page": directory_page.page,
        "total_pages": directory_page.total_pages,
        "page_size": directory_page.page_size,
        "username_query": directory_page.filters.username or "",
        "contact_query": directory_page.filters.contact or "",
        "pagination": pagination,
        "filters_active": bool(directory_page.filters.username or directory_page.filters.contact),
        "clear_filters_url": request.url.path,
        "current_url": str(request.url),
        "viewer_is_admin": session_user.user.is_admin,
        "member_avatar_urls": avatar_urls,
        "member_display_names": display_names,
    }
    return templates.TemplateResponse("members/index.html", context)


__all__ = ["router"]
