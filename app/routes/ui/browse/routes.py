from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from urllib.parse import urlencode
from sqlalchemy import desc, func, literal, or_, union_all
from sqlmodel import Session, select

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import HELP_REQUEST_STATUS_DRAFT, HelpRequest, RequestComment, User
from app.routes.ui.helpers import describe_session_role, templates
from app.services import request_comment_service, user_attribute_service
from app.routes.ui import (
    FILTER_TOPICS,
    FILTER_TOPICS_LOOKUP,
    STATUS_OPTIONS,
    STATUS_LOOKUP,
    _infer_request_topics,
    _normalize_filter_values,
    _serialize_requests,
    _truncate_text,
)

router = APIRouter(tags=["ui"])

BROWSE_PAGE_SIZE = 12
BROWSE_ALLOWED_TYPES = {"all", "requests", "comments", "profiles"}
BROWSE_TABS = [
    {"slug": "all", "label": "Everything"},
    {"slug": "requests", "label": "Requests"},
    {"slug": "comments", "label": "Comments"},
    {"slug": "profiles", "label": "Profiles"},
]


@router.get("/browse")
def browse_content(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    page: int = Query(1, ge=1),
    q: Optional[str] = Query(None),
    content_type: Optional[str] = Query("all", alias="type"),
    status: Optional[list[str]] = Query(None),
    tag: Optional[list[str]] = Query(None),
) -> Response:
    viewer = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(viewer, session_record)

    search_query = _normalize_search_term(q)
    active_tab = _sanitize_browse_tab(content_type)

    status_filters = {value for value in _normalize_filter_values(status or []) if value in STATUS_LOOKUP}
    tag_filters = {value for value in _normalize_filter_values(tag or []) if value in FILTER_TOPICS_LOOKUP}

    totals = {
        "requests": _count_requests(db, query_text=search_query, status_filters=status_filters, tag_filters=tag_filters),
        "comments": _count_comments(db, query_text=search_query, status_filters=status_filters, tag_filters=tag_filters),
        "profiles": _count_profiles(db, viewer=viewer, query_text=search_query),
    }
    totals["all"] = totals["requests"] + totals["comments"] + totals["profiles"]

    combined_page: Optional[dict[str, object]] = None
    requests_page: Optional[dict[str, object]] = None
    comments_page: Optional[dict[str, object]] = None
    profiles_page: Optional[dict[str, object]] = None

    if active_tab == "requests":
        requests_page = _fetch_request_page(
            db,
            viewer,
            page=page,
            page_size=BROWSE_PAGE_SIZE,
            query_text=search_query,
            status_filters=status_filters,
            tag_filters=tag_filters,
        )
        pagination = _build_pagination_metadata(request, requests_page["page"], requests_page["total_pages"])
    elif active_tab == "comments":
        comments_page = _fetch_comment_page(
            db,
            viewer,
            page=page,
            page_size=BROWSE_PAGE_SIZE,
            query_text=search_query,
            status_filters=status_filters,
            tag_filters=tag_filters,
        )
        pagination = _build_pagination_metadata(request, comments_page["page"], comments_page["total_pages"])
    elif active_tab == "profiles":
        profiles_page = _fetch_profile_page(
            db,
            viewer,
            page=page,
            page_size=BROWSE_PAGE_SIZE,
            query_text=search_query,
        )
        pagination = _build_pagination_metadata(request, profiles_page["page"], profiles_page["total_pages"])
    else:
        combined_page = _fetch_combined_feed(
            db,
            viewer,
            page=page,
            page_size=BROWSE_PAGE_SIZE,
            query_text=search_query,
            status_filters=status_filters,
            tag_filters=tag_filters,
            totals=totals,
        )
        pagination = _build_pagination_metadata(request, combined_page["page"], combined_page["total_pages"])

    status_options = [
        {
            "slug": option["slug"],
            "label": option["label"],
            "active": option["slug"] in status_filters,
        }
        for option in STATUS_OPTIONS
    ]
    tag_options = [
        {
            "slug": topic["slug"],
            "label": topic["label"],
            "active": topic["slug"] in tag_filters,
        }
        for topic in FILTER_TOPICS
    ]

    tabs = _build_browse_tabs(request, totals, active_tab)
    has_filters = bool(search_query or status_filters or tag_filters)

    reset_items: list[tuple[str, str]] = []
    if active_tab != "all":
        reset_items.append(("type", active_tab))
    reset_query = urlencode(reset_items, doseq=True)
    clear_filters_url = f"{request.url.path}?{reset_query}" if reset_items else request.url.path

    context = {
        "request": request,
        "user": viewer,
        "session": session_record,
        "session_role": session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "active_tab": active_tab,
        "tabs": tabs,
        "status_options": status_options,
        "tag_options": tag_options,
        "search_query": search_query or "",
        "status_filters": sorted(status_filters),
        "tag_filters": sorted(tag_filters),
        "has_filters": has_filters,
        "combined_page": combined_page,
        "requests_page": requests_page,
        "comments_page": comments_page,
        "profiles_page": profiles_page,
        "pagination": pagination,
        "topic_lookup": FILTER_TOPICS_LOOKUP,
        "filter_reset_url": clear_filters_url,
        "totals": totals,
        "viewer_is_admin": viewer.is_admin,
    }
    return templates.TemplateResponse("browse/index.html", context)


def _normalize_search_term(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _sanitize_browse_tab(value: Optional[str]) -> str:
    if not value:
        return "all"
    value = value.strip().lower()
    return value if value in BROWSE_ALLOWED_TYPES else "all"


def _build_pagination_metadata(request: Request, current_page: int, total_pages: int) -> dict[str, object]:
    total_pages = max(1, total_pages)

    def _page_url(target_page: int) -> Optional[str]:
        if target_page < 1 or target_page > total_pages:
            return None
        url = request.url.include_query_params(page=target_page)
        return str(url)

    return {
        "current": current_page,
        "total": total_pages,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_url": _page_url(current_page - 1) if current_page > 1 else None,
        "next_url": _page_url(current_page + 1) if current_page < total_pages else None,
    }


def _build_browse_tab_url(request: Request, tab_slug: str) -> str:
    current_items = list(request.query_params.multi_items()) if hasattr(request.query_params, "multi_items") else list(request.query_params.items())
    filtered = [(key, value) for key, value in current_items if key != "type"]
    if tab_slug != "all":
        filtered.append(("type", tab_slug))
    query = urlencode(filtered, doseq=True)
    return f"{request.url.path}?{query}" if query else request.url.path


def _build_browse_tabs(request: Request, tab_counts: dict[str, int], active_tab: str) -> list[dict[str, object]]:
    tabs: list[dict[str, object]] = []
    for tab in BROWSE_TABS:
        slug = tab["slug"]
        tabs.append(
            {
                "slug": slug,
                "label": tab["label"],
                "count": tab_counts.get(slug, 0),
                "url": _build_browse_tab_url(request, slug),
                "active": slug == active_tab,
            }
        )
    return tabs


def _topic_keyword_clause(columns: list, tag_filters: set[str]):  # noqa: ANN001
    if not tag_filters:
        return None
    keywords: list[str] = []
    for slug in tag_filters:
        topic = FILTER_TOPICS_LOOKUP.get(slug)
        if not topic:
            continue
        keywords.extend(topic.get("keywords", []))
    if not keywords:
        return None
    clauses = []
    for column in columns:
        for keyword in keywords:
            clauses.append(column.ilike(f"%{keyword}%"))
    if not clauses:
        return None
    return or_(*clauses)


def _build_request_browse_conditions(
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> list:
    conditions = [
        HelpRequest.status != "pending",
        HelpRequest.status != HELP_REQUEST_STATUS_DRAFT,
    ]
    if query_text:
        pattern = f"%{query_text}%"
        conditions.append(
            or_(
                HelpRequest.description.ilike(pattern),
                HelpRequest.title.ilike(pattern),
            )
        )
    if status_filters:
        conditions.append(HelpRequest.status.in_(list(status_filters)))
    topic_clause = _topic_keyword_clause([HelpRequest.description], tag_filters)
    if topic_clause is not None:
        conditions.append(topic_clause)
    return conditions


def _build_comment_browse_conditions(
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> list:
    conditions = [
        RequestComment.deleted_at.is_(None),
        HelpRequest.status != "pending",
        HelpRequest.status != HELP_REQUEST_STATUS_DRAFT,
    ]
    if query_text:
        pattern = f"%{query_text}%"
        conditions.append(
            or_(
                RequestComment.body.ilike(pattern),
                HelpRequest.description.ilike(pattern),
                HelpRequest.title.ilike(pattern),
            )
        )
    if status_filters:
        conditions.append(HelpRequest.status.in_(list(status_filters)))
    topic_clause = _topic_keyword_clause([RequestComment.body, HelpRequest.description], tag_filters)
    if topic_clause is not None:
        conditions.append(topic_clause)
    return conditions


def _profile_visibility_clause(db: Session, viewer: User):
    if viewer.is_admin:
        return None

    invitee_ids = user_attribute_service.list_invitee_user_ids(
        db,
        inviter_user_id=viewer.id,
    )
    allowed_ids = {user_id for user_id in invitee_ids if user_id}
    if viewer.id:
        allowed_ids.add(viewer.id)

    if not allowed_ids:
        return User.sync_scope == "public"

    return or_(User.sync_scope == "public", User.id.in_(list(allowed_ids)))


def _build_profile_browse_conditions(
    db: Session,
    viewer: User,
    query_text: Optional[str],
) -> list:
    conditions: list = []
    visibility_clause = _profile_visibility_clause(db, viewer)
    if visibility_clause is not None:
        conditions.append(visibility_clause)
    if query_text:
        pattern = f"%{query_text}%"
        conditions.append(
            or_(
                User.username.ilike(pattern),
                User.contact_email.ilike(pattern),
            )
        )
    return conditions


def _count_requests(
    db: Session,
    *,
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> int:
    conditions = _build_request_browse_conditions(query_text, status_filters, tag_filters)
    stmt = select(func.count()).select_from(HelpRequest).where(*conditions)
    return int(db.exec(stmt).one() or 0)


def _count_comments(
    db: Session,
    *,
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> int:
    conditions = _build_comment_browse_conditions(query_text, status_filters, tag_filters)
    stmt = (
        select(func.count())
        .select_from(RequestComment)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .where(*conditions)
    )
    return int(db.exec(stmt).one() or 0)


def _count_profiles(
    db: Session,
    *,
    viewer: User,
    query_text: Optional[str],
) -> int:
    conditions = _build_profile_browse_conditions(db, viewer, query_text)
    stmt = select(func.count()).select_from(User).where(*conditions)
    return int(db.exec(stmt).one() or 0)


def _fetch_request_page(
    db: Session,
    viewer: User,
    *,
    page: int,
    page_size: int,
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> dict[str, object]:
    total = _count_requests(db, query_text=query_text, status_filters=status_filters, tag_filters=tag_filters)
    if not total:
        return {"items": [], "page": 1, "total_pages": 1, "total": 0, "topics": {}}

    total_pages = max(1, math.ceil(total / page_size))
    current_page = min(max(1, page), total_pages)
    offset = (current_page - 1) * page_size
    stmt = (
        select(HelpRequest)
        .where(*_build_request_browse_conditions(query_text, status_filters, tag_filters))
        .order_by(HelpRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.exec(stmt).all()
    serialized = _serialize_requests(db, rows, viewer=viewer)
    topics_map = {row.id: sorted(_infer_request_topics(row)) for row in rows}
    return {
        "items": serialized,
        "page": current_page,
        "total_pages": total_pages,
        "total": total,
        "topics": topics_map,
    }


def _fetch_comment_page(
    db: Session,
    viewer: User,
    *,
    page: int,
    page_size: int,
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
) -> dict[str, object]:
    total = _count_comments(db, query_text=query_text, status_filters=status_filters, tag_filters=tag_filters)
    if not total:
        return {"items": [], "page": 1, "total_pages": 1, "total": 0}

    total_pages = max(1, math.ceil(total / page_size))
    current_page = min(max(1, page), total_pages)
    offset = (current_page - 1) * page_size
    stmt = (
        select(RequestComment, User, HelpRequest)
        .join(User, User.id == RequestComment.user_id)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .where(*_build_comment_browse_conditions(query_text, status_filters, tag_filters))
        .order_by(RequestComment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.exec(stmt).all()
    entries = []
    for comment, author, help_request in rows:
        payload = request_comment_service.serialize_comment(comment, author)
        entries.append(
            {
                "comment": payload,
                "request": {
                    "id": help_request.id,
                    "title": help_request.title or "Untitled request",
                    "status": help_request.status,
                },
            }
        )
    return {
        "items": entries,
        "page": current_page,
        "total_pages": total_pages,
        "total": total,
    }


def _fetch_profile_page(
    db: Session,
    viewer: User,
    *,
    page: int,
    page_size: int,
    query_text: Optional[str],
) -> dict[str, object]:
    total = _count_profiles(db, viewer=viewer, query_text=query_text)
    if not total:
        return {
            "items": [],
            "page": 1,
            "total_pages": 1,
            "total": 0,
            "avatars": {},
        }

    total_pages = max(1, math.ceil(total / page_size))
    current_page = min(max(1, page), total_pages)
    offset = (current_page - 1) * page_size
    stmt = (
        select(User)
        .where(*_build_profile_browse_conditions(db, viewer, query_text))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = db.exec(stmt).all()
    avatar_urls = user_attribute_service.load_profile_photo_urls(
        db,
        user_ids=[user.id for user in rows if user.id],
    )
    return {
        "items": rows,
        "page": current_page,
        "total_pages": total_pages,
        "total": total,
        "avatars": avatar_urls,
    }


def _load_requests_by_ids(db: Session, viewer: User, request_ids: list[int]) -> dict[int, dict[str, object]]:
    if not request_ids:
        return {}
    stmt = (
        select(HelpRequest)
        .where(HelpRequest.id.in_(request_ids))
        .where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
    )
    rows = db.exec(stmt).all()
    serialized = _serialize_requests(db, rows, viewer=viewer)
    topics_map = {row.id: sorted(_infer_request_topics(row)) for row in rows}
    return {
        item["id"]: {
            "data": item,
            "topics": topics_map.get(item["id"], []),
        }
        for item in serialized
    }


def _load_comments_by_ids(db: Session, comment_ids: list[int]) -> dict[int, dict[str, object]]:
    if not comment_ids:
        return {}
    stmt = (
        select(RequestComment, User, HelpRequest)
        .join(User, User.id == RequestComment.user_id)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .where(RequestComment.id.in_(comment_ids))
        .where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
    )
    rows = db.exec(stmt).all()
    lookup: dict[int, dict[str, object]] = {}
    for comment, author, help_request in rows:
        payload = request_comment_service.serialize_comment(comment, author)
        lookup[comment.id] = {
            "comment": payload,
            "request": {
                "id": help_request.id,
                "title": help_request.title or "Untitled request",
                "status": help_request.status,
            },
        }
    return lookup


def _load_profiles_by_ids(db: Session, viewer: User, profile_ids: list[int]) -> dict[int, dict[str, object]]:
    if not profile_ids:
        return {}
    stmt = select(User).where(User.id.in_(profile_ids))
    rows = db.exec(stmt).all()
    avatar_urls = user_attribute_service.load_profile_photo_urls(
        db,
        user_ids=[user.id for user in rows if user.id],
    )
    return {
        user.id: {
            "user": user,
            "avatar_url": avatar_urls.get(user.id),
        }
        for user in rows
        if user.id is not None
    }


def _fetch_combined_feed(
    db: Session,
    viewer: User,
    *,
    page: int,
    page_size: int,
    query_text: Optional[str],
    status_filters: set[str],
    tag_filters: set[str],
    totals: dict[str, int],
) -> dict[str, object]:
    total = totals.get("all", 0)
    if not total:
        return {"items": [], "page": 1, "total_pages": 1, "total": 0}

    total_pages = max(1, math.ceil(total / page_size))
    current_page = min(max(1, page), total_pages)
    offset = (current_page - 1) * page_size

    request_select = (
        select(
            literal("request").label("kind"),
            HelpRequest.id.label("entity_id"),
            HelpRequest.created_at.label("created_at"),
        )
        .where(*_build_request_browse_conditions(query_text, status_filters, tag_filters))
    )
    comment_select = (
        select(
            literal("comment").label("kind"),
            RequestComment.id.label("entity_id"),
            RequestComment.created_at.label("created_at"),
        )
        .select_from(RequestComment)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .where(*_build_comment_browse_conditions(query_text, status_filters, tag_filters))
    )
    profile_select = (
        select(
            literal("profile").label("kind"),
            User.id.label("entity_id"),
            User.created_at.label("created_at"),
        )
        .where(*_build_profile_browse_conditions(db, viewer, query_text))
    )

    combined_source = union_all(request_select, comment_select, profile_select).subquery()
    stmt = (
        select(
            combined_source.c.kind,
            combined_source.c.entity_id,
            combined_source.c.created_at,
        )
        .order_by(desc(combined_source.c.created_at))
        .offset(offset)
        .limit(page_size)
    )
    rows = db.exec(stmt).all()

    request_ids = [row.entity_id for row in rows if row.kind == "request"]
    comment_ids = [row.entity_id for row in rows if row.kind == "comment"]
    profile_ids = [row.entity_id for row in rows if row.kind == "profile"]

    request_lookup = _load_requests_by_ids(db, viewer, request_ids)
    comment_lookup = _load_comments_by_ids(db, comment_ids)
    profile_lookup = _load_profiles_by_ids(db, viewer, profile_ids)

    entries: list[dict[str, object]] = []
    for row in rows:
        if row.kind == "request":
            payload = request_lookup.get(row.entity_id)
            if not payload:
                continue
            entries.append(
                {
                    "kind": "request",
                    "data": payload["data"],
                    "created_at": row.created_at,
                    "topics": payload["topics"],
                    "href": f"/requests/{payload['data']['id']}",
                    "snippet": _truncate_text(str(payload["data"].get("description") or "")),
                }
            )
        elif row.kind == "comment":
            payload = comment_lookup.get(row.entity_id)
            if not payload:
                continue
            entries.append(
                {
                    "kind": "comment",
                    "data": payload["comment"],
                    "created_at": row.created_at,
                    "request": payload["request"],
                    "href": f"/comments/{payload['comment']['id']}",
                    "snippet": _truncate_text(str(payload["comment"].get("body") or "")),
                }
            )
        elif row.kind == "profile":
            payload = profile_lookup.get(row.entity_id)
            if not payload:
                continue
            profile_user = payload["user"]
            if viewer.is_admin:
                profile_href = f"/admin/profiles/{profile_user.id}"
            elif profile_user.id == viewer.id:
                profile_href = "/profile"
            else:
                profile_href = f"/people/{profile_user.username}"
            entries.append(
                {
                    "kind": "profile",
                    "user": payload["user"],
                    "avatar_url": payload["avatar_url"],
                    "created_at": row.created_at,
                    "href": profile_href,
                }
            )

    return {
        "items": entries,
        "page": current_page,
        "total_pages": total_pages,
        "total": total,
    }
