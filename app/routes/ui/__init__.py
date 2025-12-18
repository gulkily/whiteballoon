from __future__ import annotations

import json
import logging
import math
import re
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Annotated, Iterable, Literal, Optional, Sequence, cast
from urllib.parse import urlencode, urlparse
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, literal, or_, union_all
from sqlmodel import Session, select

from app.dependencies import (
    SessionDep,
    SessionUser,
    get_current_session,
    require_authenticated_user,
    require_admin,
    require_session_user,
)
from app.models import (
    AuthenticationRequest,
    CommentPromotion,
    HELP_REQUEST_STATUS_DRAFT,
    HelpRequest,
    RecurringRequestDeliveryMode,
    RequestComment,
    User,
    UserAttribute,
    UserSession,
)
from app.modules.requests import services as request_services
from app.modules.requests.routes import RequestResponse, calculate_can_complete
from app.captions import (
    build_caption_payload,
    load_preferences as load_caption_preferences,
)
from app.captions import load_preferences as load_caption_preferences
from app.services import (
    auth_service,
    caption_preference_service,
    chat_reaction_parser,
    comment_llm_insights_service,
    comment_request_promotion_service,
    invite_graph_service,
    invite_map_cache_service,
    recurring_template_service,
    request_chat_search_service,
    request_chat_suggestions,
    request_channel_metrics,
    request_channel_presence,
    request_channel_reads,
    request_pin_service,
    request_comment_service,
    tag_color_service,
    signal_profile_snapshot_service,
    user_attribute_service,
    user_profile_highlight_service,
    vouch_service,
    rss_feed_token_service,
    rss_feed_catalog,
)
from app import config
from app.url_utils import build_invite_link, generate_qr_code_data_url, get_base_url
from .helpers import describe_session_role, templates

router = APIRouter(tags=["ui"])

logger = logging.getLogger(__name__)

CHAT_SEARCH_MIN_COMMENTS = 5

FILTER_TOPICS = [
    {"slug": "groceries", "label": "Groceries", "keywords": ["grocery", "groceries", "food", "meal", "produce"]},
    {"slug": "rides", "label": "Transportation", "keywords": ["ride", "carpool", "transport", "drive", "pickup"]},
    {"slug": "housing", "label": "Housing", "keywords": ["room", "housing", "shelter", "rent"]},
    {"slug": "health", "label": "Health", "keywords": ["medical", "health", "doctor", "medicine"]},
    {"slug": "childcare", "label": "Childcare", "keywords": ["child", "kid", "babysit", "school"]},
]

FILTER_TOPICS_LOOKUP = {topic["slug"]: topic for topic in FILTER_TOPICS}

URGENCY_LEVELS = [
    {"slug": "urgent", "label": "Urgent", "keywords": ["urgent", "asap", "immediately", "tonight", "today"]},
    {"slug": "soon", "label": "Soon", "keywords": ["tomorrow", "this week", "next few", "soon"]},
    {"slug": "flexible", "label": "Flexible", "keywords": []},
]

STATUS_OPTIONS = [
    {"slug": "open", "label": "Open"},
    {"slug": "completed", "label": "Completed"},
]

STATUS_LOOKUP = {status_option["slug"]: status_option for status_option in STATUS_OPTIONS}

BROWSE_PAGE_SIZE = 12
BROWSE_ALLOWED_TYPES = {"all", "requests", "comments", "profiles"}
BROWSE_TABS = [
    {"slug": "all", "label": "Everything"},
    {"slug": "requests", "label": "Requests"},
    {"slug": "comments", "label": "Comments"},
    {"slug": "profiles", "label": "Profiles"},
]

CHANNEL_RECENT_COMMENT_LIMIT = 50


class ChannelPresencePayload(BaseModel):
    request_id: int
    typing: bool = False


def _normalize_filter_values(values: list[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


def _request_description_text(help_request: HelpRequest) -> str:
    """Return the help request description without inline reaction suffixes."""
    clean_text, _ = chat_reaction_parser.strip_reactions(help_request.description or "")
    return clean_text


def _infer_request_topics(help_request: HelpRequest) -> set[str]:
    description = _request_description_text(help_request).lower()
    topics: set[str] = set()
    for topic in FILTER_TOPICS:
        if any(keyword in description for keyword in topic["keywords"]):
            topics.add(topic["slug"])
    return topics


def _infer_request_urgency(help_request: HelpRequest) -> str:
    description = _request_description_text(help_request).lower()
    for level in URGENCY_LEVELS:
        if level["keywords"] and any(keyword in description for keyword in level["keywords"]):
            return level["slug"]
    return "flexible"


def _resolve_redirect_target(next_url: Optional[str], fallback: str = "/") -> str:
    if next_url and next_url.startswith("/"):
        return next_url
    if next_url:
        parsed = urlparse(next_url)
        if parsed.path:
            return parsed.path
    return fallback


def _redirect_back(request: Request, next_url: Optional[str] = None) -> RedirectResponse:
    fallback = request.headers.get("referer") or request.url.path
    target = _resolve_redirect_target(next_url, fallback=fallback)
    return RedirectResponse(url=target, status_code=status.HTTP_303_SEE_OTHER)


def _matches_request_filters(
    topics: set[str],
    urgency: str,
    status_value: str,
    topic_filters: set[str],
    urgency_filters: set[str],
    status_filters: set[str],
) -> bool:
    if topic_filters and topics.isdisjoint(topic_filters):
        return False
    if urgency_filters and urgency not in urgency_filters:
        return False
    if status_filters and status_value not in status_filters:
        return False
    return True


def _build_filter_url(
    base_path: str,
    current_items: list[tuple[str, str]],
    field: str,
    value: str,
    active: bool,
) -> str:
    preserved = [
        (key, val) for key, val in current_items if not (key == field and val.lower() == value.lower())
    ]
    preserved = [(k, v) for (k, v) in preserved if k != "page"]
    if not active:
        preserved.append((field, value))
    query = urlencode(preserved, doseq=True)
    return f"{base_path}?{query}" if query else base_path


def _build_reset_url(base_path: str, current_items: list[tuple[str, str]]) -> str:
    filtered = [
        (key, val)
        for key, val in current_items
        if key not in {"topic", "urgency", "status", "page"}
    ]
    query = urlencode(filtered, doseq=True)
    return f"{base_path}?{query}" if query else base_path


def _trim_request_title(help_request: HelpRequest) -> str:
    explicit = (help_request.title or "").strip()
    if explicit:
        return explicit
    description = _request_description_text(help_request).strip()
    if not description:
        return f"Request #{help_request.id}" if help_request.id else "Request"
    first_line = description.splitlines()[0].strip()
    condensed = re.sub(r"\s+", " ", first_line)
    if len(condensed) <= 96:
        return condensed
    return condensed[:93].rstrip() + "…"


def _build_signal_ledger_metrics(requests: Sequence[HelpRequest]) -> dict[str, object]:
    total = len(requests)
    open_count = sum(1 for item in requests if item.status == "open")
    completed_count = sum(1 for item in requests if item.status == "completed")
    contact_ready = sum(1 for item in requests if (item.contact_email or "").strip())
    verified_count = sum(1 for item in requests if getattr(item, "sync_scope", "private") != "private")

    def _percent(numerator: int, denominator: int) -> int:
        if denominator <= 0:
            return 0
        return int(round((numerator / denominator) * 100))

    network_health = _percent(completed_count, total)
    capital_share = _percent(contact_ready, total)
    verification_rate = _percent(verified_count, total)
    return {
        "total_requests": total,
        "network_health": {
            "value": network_health,
            "unit": "%",
            "delta": completed_count - open_count,
            "delta_positive": completed_count >= open_count,
            "meta": f"{completed_count} completed / {open_count} open",
        },
        "capital_flows": {
            "value": contact_ready,
            "unit": "cases",
            "delta": capital_share,
            "delta_positive": capital_share >= 50,
            "meta": f"{capital_share}% include contact handoffs",
        },
        "verification_chain": {
            "value": verification_rate,
            "unit": "%",
            "delta": verified_count,
            "delta_positive": verified_count >= (total // 2 if total else 0),
            "meta": f"{verified_count} in shared scope",
        },
    }


def _build_signal_ledger_timeline(requests: Sequence[HelpRequest]) -> list[dict[str, object]]:
    sorted_requests = sorted(requests, key=lambda item: item.updated_at, reverse=True)
    timeline: list[dict[str, object]] = []
    for help_request in sorted_requests[:8]:
        timeline.append(
            {
                "id": help_request.id,
                "title": _trim_request_title(help_request),
                "status": help_request.status,
                "updated_at": help_request.updated_at,
                "sync_scope": getattr(help_request, "sync_scope", "private"),
                "has_contact": bool((help_request.contact_email or "").strip()),
            }
        )
    return timeline


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


def _profile_visibility_clause(db: Session, viewer: User):  # noqa: ANN001
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


def _truncate_text(text: str, limit: int = 220) -> str:
    snippet = (text or "").strip()
    if len(snippet) <= limit:
        return snippet
    trimmed = snippet[: max(0, limit - 3)].rstrip()
    return f"{trimmed}..."


def _serialize_requests(
    db: Session,
    items: Sequence[HelpRequest] | None = None,
    viewer: Optional[User] = None,
    pin_map: Optional[dict[int, request_pin_service.PinMetadata]] = None,
    *,
    limit: int | None = 50,
    search: str | None = None,
    statuses: Optional[Iterable[str]] = None,
    pinned_only: bool = False,
):
    if items is None:
        items = request_services.list_requests(
            db,
            limit=limit,
            search=search,
            statuses=statuses,
            pinned_only=pinned_only,
        )
    creator_usernames = request_services.load_creator_usernames(db, items)
    creator_display_names = _map_request_creator_display_names(db, items)
    request_ids = [item.id for item in items if item.id]
    template_metadata = recurring_template_service.load_template_metadata(db, request_ids)
    serialized = []
    for item in items:
        can_complete = calculate_can_complete(item, viewer) if viewer else False
        pin_metadata = pin_map.get(item.id) if pin_map else None
        template_info = template_metadata.get(item.id) if template_metadata else None
        serialized.append(
            RequestResponse.from_model(
                item,
                created_by_username=creator_usernames.get(item.created_by_user_id),
                created_by_display_name=creator_display_names.get(item.id),
                can_complete=can_complete,
                is_pinned=pin_metadata is not None,
                pin_rank=pin_metadata.rank if pin_metadata else None,
                recurring_template_id=template_info.get("template_id") if template_info else None,
                recurring_template_title=template_info.get("template_title") if template_info else None,
            ).model_dump()
        )
    return serialized


def _map_request_creator_display_names(db: Session, requests: Sequence[HelpRequest]) -> dict[int, str]:
    grouped: dict[str, set[int]] = {}
    for req in requests:
        if not req or not req.created_by_user_id:
            continue
        attr_key = _signal_display_attr_key(req)
        if not attr_key:
            continue
        grouped.setdefault(attr_key, set()).add(req.created_by_user_id)
    resolved: dict[str, dict[int, str]] = {}
    for attr_key, user_ids in grouped.items():
        resolved[attr_key] = _load_signal_display_names_for_user_ids(db, user_ids, attr_key)
    mapping: dict[int, str] = {}
    for req in requests:
        if not req or not req.id or not req.created_by_user_id:
            continue
        attr_key = _signal_display_attr_key(req)
        if not attr_key:
            continue
        display_name = resolved.get(attr_key, {}).get(req.created_by_user_id)
        if display_name:
            mapping[req.id] = display_name
    return mapping


def _build_request_channel_rows(
    requests: list[dict[str, object]],
    *,
    comment_counts: Optional[dict[int, int]] = None,
    unread_counts: Optional[dict[int, int]] = None,
    read_counts: Optional[dict[int, int]] = None,
) -> list[dict[str, object]]:
    ordered_rows: list[tuple[int, dict[str, object]]] = []
    for index, item in enumerate(requests):
        description = (item.get("description") or "").strip()
        first_line = description.splitlines()[0].strip() if description else ""
        title = first_line or f"Request #{item.get('id')}"
        request_id = int(item.get("id")) if item.get("id") else None
        unread_total = unread_counts.get(request_id, 0) if (unread_counts and request_id) else 0
        if read_counts and request_id in read_counts:
            unread_total = max((comment_counts or {}).get(request_id, 0) - read_counts[request_id], 0)
        row = {
            "id": request_id,
            "title": title[:120],
            "preview": _truncate_text(description, limit=160),
            "status": item.get("status"),
            "updated_at": item.get("updated_at"),
            "is_pinned": bool(item.get("is_pinned")),
            "pin_rank": item.get("pin_rank"),
            "comment_count": (comment_counts.get(request_id, 0) if (comment_counts and request_id) else 0),
            "unread_count": unread_total,
        }
        ordered_rows.append((index, row))

    def _sort_key(payload: tuple[int, dict[str, object]]) -> tuple[int, float]:
        idx, row = payload
        is_pinned = bool(row.get("is_pinned"))
        rank = row.get("pin_rank")
        if isinstance(rank, int):
            rank_key = float(rank)
        else:
            rank_key = float(idx)
        return (0 if is_pinned else 1, rank_key if is_pinned else float(idx))

    ordered_rows.sort(key=_sort_key)
    return [row for _, row in ordered_rows]


def _build_request_channel_chat_context(
    request: Request,
    db: Session,
    session_user: SessionUser,
    help_request: HelpRequest,
) -> dict[str, object]:
    detail_context = _build_request_detail_context(
        request,
        db,
        session_user,
        help_request,
        page=1,
        recent_limit=CHANNEL_RECENT_COMMENT_LIMIT,
    )
    request_item = detail_context.get("request_item")
    if isinstance(request_item, RequestResponse):
        request_payload = request_item.model_dump()
    else:
        request_payload = request_item
    return {
        "request": request_payload,
        "comments": detail_context.get("comments", []),
        "can_comment": detail_context.get("can_comment", False),
        "can_promote_comments": detail_context.get("can_promote_comments", False),
        "comment_form_errors": detail_context.get("comment_form_errors", []),
        "comment_form_body": detail_context.get("comment_form_body", ""),
        "comment_max_length": detail_context.get("comment_max_length"),
        "comment_display_names": detail_context.get("comment_display_names", {}),
        "comment_promotions": detail_context.get("comment_promotions", {}),
        "session_username": detail_context.get("session_username"),
        "session_avatar_url": detail_context.get("session_avatar_url"),
    }


def _format_proof_receipts(proof_points: list[dict[str, str]] | None) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    if not proof_points:
        return receipts
    for point in proof_points:
        label = str(point.get("label", "")).strip()
        detail = str(point.get("detail", "")).strip()
        reference = str(point.get("reference", "")).strip()
        href: Optional[str] = None
        display_ref = reference
        external = False
        ref_lower = reference.lower()
        if ref_lower.startswith("http"):
            href = reference
            external = True
            parsed = urlparse(reference)
            display_ref = parsed.netloc or reference
        elif ref_lower.startswith("request#"):
            digits = "".join(ch for ch in reference if ch.isdigit())
            if digits:
                href = f"/requests/{digits}"
                display_ref = f"Request #{digits}"
        elif reference.isdigit():
            href = f"/requests/{reference}"
            display_ref = f"Request #{reference}"
        receipts.append(
            {
                "label": label,
                "detail": detail,
                "reference": reference,
                "href": href,
                "display_ref": display_ref,
                "external": external,
            }
        )
    return receipts


def _format_snapshot_links(entries) -> list[dict[str, object]]:  # noqa: ANN001
    links: list[dict[str, object]] = []
    if not entries:
        return links
    for entry in entries:
        url = str(getattr(entry, "url", "") or "").strip()
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        domain = (getattr(entry, "domain", "") or parsed.netloc or url).lower()
        safe_url = parsed.geturl()
        links.append(
            {
                "domain": domain,
                "href": safe_url,
                "count": getattr(entry, "count", 0) or 0,
            }
        )
    return links


def _build_request_ctas(request_ids: list[int], user_id: int) -> list[dict[str, object]]:
    chips: list[dict[str, object]] = []
    seen: set[int] = set()
    for request_id in request_ids:
        if request_id in seen:
            continue
        seen.add(request_id)
        chips.append(
            {
                "request_id": request_id,
                "href": f"/requests/{request_id}?chat_participant={user_id}",
            }
        )
        if len(chips) >= 3:
            break
    return chips


def _parse_insight_filters(request: Request) -> dict[str, set[str]]:
    params = request.query_params
    return {
        "resource": {value.lower() for value in params.getlist("insight_resource") if value},
        "request": {value.lower() for value in params.getlist("insight_request") if value},
        "urgency": {value.lower() for value in params.getlist("insight_urgency") if value},
        "sentiment": {value.lower() for value in params.getlist("insight_sentiment") if value},
    }


def _insight_filters_active(filters: dict[str, set[str]]) -> bool:
    return any(values for values in filters.values())


def _matches_insight_filters(comment_payload: dict[str, object], filters: dict[str, set[str]]) -> bool:
    metadata = comment_payload.get("insight_metadata") or {}
    return _insight_metadata_matches(metadata, filters)


def _insight_metadata_matches(metadata: dict[str, object], filters: dict[str, set[str]]) -> bool:
    resource_tags = set(metadata.get("resource_tags") or [])
    request_tags = set(metadata.get("request_tags") or [])
    urgency = (metadata.get("urgency") or "").lower()
    sentiment = (metadata.get("sentiment") or "").lower()

    if filters["resource"] and resource_tags.isdisjoint(filters["resource"]):
        return False
    if filters["request"] and request_tags.isdisjoint(filters["request"]):
        return False
    if filters["urgency"] and urgency not in filters["urgency"]:
        return False
    if filters["sentiment"] and sentiment not in filters["sentiment"]:
        return False
    return True


def _record_tag_summary(
    storage: dict[str, dict[str, object]],
    tag_entry: tag_color_service.TagHue,
    comment_id: int,
) -> None:
    label = (tag_entry.label or "").strip()
    slug = tag_entry.slug
    if not (label and slug):
        return
    entry = storage.get(slug)
    if not entry:
        entry = {
            "label": label,
            "slug": slug,
            "count": 0,
            "comment_id": comment_id,
            "hue": tag_entry.hue,
        }
        storage[slug] = entry
    entry["count"] += 1


def _format_tag_summary(storage: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    items = [
        {
            "label": data.get("label") or label,
            "count": data["count"],
            "href": f"/comments/{data['comment_id']}",
            "slug": data.get("slug") or label,
            "hue": data.get("hue"),
        }
        for label, data in storage.items()
    ]
    items.sort(key=lambda item: (-item["count"], item["label"]))
    return items


def _format_value_counts(counter: Counter[str]) -> list[dict[str, object]]:
    items = []
    for raw_label, count in counter.items():
        label = (raw_label or "").strip()
        if not label:
            continue
        items.append({"label": label.title(), "count": count})
    items.sort(key=lambda item: (-item["count"], item["label"]))
    return items


def _build_request_comment_insights_summary(help_request_id: int) -> Optional[dict[str, object]]:
    analyses = comment_llm_insights_service.list_analyses_for_request(help_request_id)
    if not analyses:
        return None

    resource_counts: dict[str, dict[str, object]] = {}
    request_counts: dict[str, dict[str, object]] = {}
    urgency_counts: Counter[str] = Counter()
    sentiment_counts: Counter[str] = Counter()

    for analysis in analyses:
        for tag_entry in analysis.resource_tag_hues():
            _record_tag_summary(resource_counts, tag_entry, analysis.comment_id)
        for tag_entry in analysis.request_tag_hues():
            _record_tag_summary(request_counts, tag_entry, analysis.comment_id)
        if analysis.urgency:
            urgency_counts[analysis.urgency] += 1
        if analysis.sentiment:
            sentiment_counts[analysis.sentiment] += 1

    summary = {
        "resource_tags": _format_tag_summary(resource_counts),
        "request_tags": _format_tag_summary(request_counts),
        "urgency": _format_value_counts(urgency_counts),
        "sentiment": _format_value_counts(sentiment_counts),
    }

    if not (summary["resource_tags"] or summary["request_tags"] or summary["urgency"] or summary["sentiment"]):
        return None
    return summary


def _build_comment_insights_lookup(help_request_id: int) -> dict[int, dict[str, object]]:
    analyses = comment_llm_insights_service.list_analyses_for_request(help_request_id)
    return {
        analysis.comment_id: {
            "resource_tags": [tag.lower() for tag in analysis.resource_tags],
            "request_tags": [tag.lower() for tag in analysis.request_tags],
            "urgency": (analysis.urgency or "").lower(),
            "sentiment": (analysis.sentiment or "").lower(),
        }
        for analysis in analyses
    }

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

    if session_record.is_fully_authenticated:
        settings = config.get_settings()
        if settings.request_channels_enabled:
            return RedirectResponse(url="/requests/channels", status_code=status.HTTP_303_SEE_OTHER)

    session_role = describe_session_role(user, session_record)
    return _render_requests_page(request, db, user, session_record, session_role)


@router.get("/brand/logo", include_in_schema=False)
def logo_capture(request: Request) -> Response:
    """Render a padded, standalone logo for easy screenshots."""
    return templates.TemplateResponse("branding/logo_capture.html", {"request": request})


@router.get("/brand/logo/flat", include_in_schema=False)
def logo_capture_flat(request: Request) -> Response:
    """Render a flat, rectangular logo layout for screenshots."""
    return templates.TemplateResponse("branding/logo_capture_flat.html", {"request": request})


@router.get("/requests")
def requests_feed(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    user = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(user, session_record)
    return _render_requests_page(request, db, user, session_record, session_role)


def _render_requests_page(
    request: Request,
    db: SessionDep,
    user: User,
    session_record: UserSession,
    session_role: Optional[dict[str, str]],
) -> Response:
    session_avatar_url = _get_account_avatar(db, user.id)
    caption_prefs = load_caption_preferences(db, user.id)
    rss_feed_entries = _load_rss_feed_entries(request, db, user)
    rss_feed_links = _build_rss_link_metadata(rss_feed_entries)

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
            "caption_preferences": caption_prefs,
            "requests_caption": build_caption_payload(
                caption_prefs,
                caption_id="requests_hero_intro",
                text="View the latest needs below or add a new one.",
            ),
            "rss_feed_links": rss_feed_links,
        }
        return templates.TemplateResponse("requests/pending.html", context)

    query_params = request.query_params
    topic_filters = _normalize_filter_values(query_params.getlist("topic"))
    urgency_filters = _normalize_filter_values(query_params.getlist("urgency"))
    status_filters = _normalize_filter_values(query_params.getlist("status"))
    all_query_items = list(query_params.multi_items()) if hasattr(query_params, "multi_items") else list(query_params.items())

    request_objects = request_services.list_requests(db)
    enriched_requests: list[tuple[HelpRequest, set[str], str]] = []
    topic_counts: Counter[str] = Counter()
    urgency_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for help_request in request_objects:
        topics = _infer_request_topics(help_request)
        urgency = _infer_request_urgency(help_request)
        for slug in topics:
            topic_counts[slug] += 1
        urgency_counts[urgency] += 1
        status_counts[help_request.status] += 1
        enriched_requests.append((help_request, topics, urgency))

    filtered_objects = [
        help_request
        for help_request, topics, urgency in enriched_requests
        if _matches_request_filters(topics, urgency, help_request.status, topic_filters, urgency_filters, status_filters)
    ]

    pin_map = request_pin_service.get_pin_map(db)
    public_requests = _serialize_requests(db, filtered_objects, viewer=user, pin_map=pin_map)
    pinned_records = request_pin_service.list_pinned_requests(
        db,
        limit=config.get_settings().pinned_requests_limit,
    )
    pinned_ids = {record.request.id for record in pinned_records}
    pinned_requests = _serialize_requests(
        db,
        [record.request for record in pinned_records],
        viewer=user,
        pin_map=pin_map,
    )
    if pinned_ids:
        public_requests = [item for item in public_requests if item.get("id") not in pinned_ids]

    filter_options = {
        "topics": [],
        "urgency": [],
        "status": [],
    }
    base_path = request.url.path
    for topic in FILTER_TOPICS:
        slug = topic["slug"]
        active = slug in topic_filters
        url = _build_filter_url(base_path, all_query_items, "topic", slug, active)
        filter_options["topics"].append(
            {
                "slug": slug,
                "label": topic["label"],
                "active": active,
                "count": topic_counts.get(slug, 0),
                "url": url,
            }
        )
    for level in URGENCY_LEVELS:
        slug = level["slug"]
        active = slug in urgency_filters
        url = _build_filter_url(base_path, all_query_items, "urgency", slug, active)
        filter_options["urgency"].append(
            {
                "slug": slug,
                "label": level["label"],
                "active": active,
                "count": urgency_counts.get(slug, 0),
                "url": url,
            }
        )
    for status_option in STATUS_OPTIONS:
        slug = status_option["slug"]
        active = slug in status_filters
        url = _build_filter_url(base_path, all_query_items, "status", slug, active)
        filter_options["status"].append(
            {
                "slug": slug,
                "label": status_option["label"],
                "active": active,
                "count": status_counts.get(slug, 0),
                "url": url,
            }
        )

    reset_url = _build_reset_url(base_path, all_query_items)
    filters_active = bool(topic_filters or urgency_filters or status_filters)
    show_pinned_section = not filters_active
    pinned_payload = pinned_requests if show_pinned_section else []
    signal_ledger_metrics = _build_signal_ledger_metrics(filtered_objects)
    signal_ledger_timeline = _build_signal_ledger_timeline(filtered_objects)
    draft_requests = _serialize_requests(
        db,
        request_services.list_drafts_for_user(db, user_id=user.id),
        viewer=user,
    )
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
            "caption_preferences": caption_prefs,
            "requests_caption": build_caption_payload(
                caption_prefs,
                caption_id="requests_hero_intro",
                text="View the latest needs below or add a new one.",
            ),
            "filter_options": filter_options,
            "active_filters": {
                "topics": sorted(topic_filters),
                "urgency": sorted(urgency_filters),
                "status": sorted(status_filters),
            },
            "filter_reset_url": reset_url,
            "pinned_requests": pinned_payload,
            "show_pinned_section": show_pinned_section,
            "can_pin_requests": user.is_admin,
            "pinned_request_count": len(pinned_payload),
            "signal_ledger_metrics": signal_ledger_metrics,
            "signal_ledger_timeline": signal_ledger_timeline,
            "draft_requests": draft_requests,
            "rss_feed_links": rss_feed_links,
        },
    )


@router.get("/requests/channels")
def request_channels_workspace(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    request_id: int | None = Query(None, alias="channel"),
) -> Response:
    settings = config.get_settings()
    if not settings.request_channels_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request channels disabled")

    viewer = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(viewer, session_record)

    request_objects = request_services.list_requests(db)
    pin_map = request_pin_service.get_pin_map(db)
    serialized_requests = _serialize_requests(db, request_objects, viewer=viewer, pin_map=pin_map)
    request_ids = [int(item["id"]) for item in serialized_requests if item.get("id")]
    comment_counts, unread_counts = request_channel_metrics.load_comment_counts(
        db,
        request_ids,
        newer_than=session_record.last_seen_at,
    )
    read_counts = request_channel_reads.get_read_counts(session_record.id, request_ids)
    request_lookup = {help_request.id: help_request for help_request in request_objects if help_request.id}
    channel_rows = _build_request_channel_rows(
        serialized_requests,
        comment_counts=comment_counts,
        unread_counts=unread_counts,
        read_counts=read_counts,
    )

    active_channel_id = request_id
    if active_channel_id is None and channel_rows:
        active_channel_id = channel_rows[0]["id"]

    active_channel = None
    active_request_payload = None
    active_chat_context = None
    if active_channel_id is not None:
        active_channel = next((row for row in channel_rows if row["id"] == active_channel_id), None)
        active_request_payload = next(
            (item for item in serialized_requests if item["id"] == active_channel_id),
            None,
        )
        help_request = request_lookup.get(active_channel_id)
        if help_request:
            active_chat_context = _build_request_channel_chat_context(
                request,
                db,
                session_user,
                help_request,
            )
        request_channel_reads.mark_read(
            session_record.id,
            active_channel_id,
            comment_count=comment_counts.get(active_channel_id, 0),
        )

    rss_feed_entries = _load_rss_feed_entries(request, db, viewer)
    rss_feed_links = _build_rss_link_metadata(rss_feed_entries)

    context = {
        "request": request,
        "user": viewer,
        "session": session_record,
        "session_role": session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "channel_requests": channel_rows,
        "channel_requests_json": json.dumps(channel_rows),
        "active_channel": active_channel,
        "active_channel_request": active_request_payload,
        "active_channel_id": active_channel_id,
        "active_chat_context": active_chat_context,
        "rss_feed_links": rss_feed_links,
    }
    return templates.TemplateResponse("requests/channels.html", context)


@router.get("/requests/channels/{request_id}/panel")
def request_channel_panel(
    request: Request,
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    settings = config.get_settings()
    if not settings.request_channels_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request channels disabled")

    help_request = request_services.get_request_by_id(db, request_id=request_id)
    chat_context = _build_request_channel_chat_context(request, db, session_user, help_request)
    request_channel_reads.mark_read(
        session_user.session.id,
        help_request.id,
        comment_count=len(chat_context.get("comments", [])),
    )
    template = templates.get_template("requests/partials/channel_chat.html")
    html = template.render({"request": request, "user": session_user.user, "chat": chat_context})

    channel_meta = {
        "id": chat_context["request"].get("id"),
        "comment_count": len(chat_context.get("comments", [])),
        "status": chat_context["request"].get("status"),
    }
    return JSONResponse({"html": html, "channel": channel_meta})


@router.post("/requests/channels/presence")
def update_request_channel_presence(
    payload: ChannelPresencePayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    settings = config.get_settings()
    if not settings.request_channels_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request channels disabled")
    request_channel_presence.mark_presence(session_user.user, payload.request_id, typing=payload.typing)
    return JSONResponse({"ok": True})


@router.get("/requests/channels/presence")
def get_request_channel_presence(
    id: list[int] = Query([], alias="id"),
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    settings = config.get_settings()
    if not settings.request_channels_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request channels disabled")
    if not id:
        return JSONResponse({"presence": {}})
    presence = request_channel_presence.list_presence(id)
    return JSONResponse({"presence": presence})


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


@router.get("/requests/recurring")
def recurring_requests_page(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    viewer = session_user.user
    session_record = session_user.session
    template_list = recurring_template_service.list_templates_for_user(db, user_id=viewer.id)
    delivery_modes = list(RecurringRequestDeliveryMode)
    interval_options = _recurring_interval_options()
    prepared_templates: list[dict[str, object]] = []
    for template in template_list:
        preset = _match_interval_preset(template.interval_minutes)
        custom_value, custom_unit = _minutes_to_custom_interval(template.interval_minutes)
        prepared_templates.append(
            {
                "record": template,
                "interval_preset": preset,
                "custom_interval_value": custom_value,
                "custom_interval_unit": custom_unit,
            }
        )
    context = {
        "request": request,
        "user": viewer,
        "session": session_record,
        "session_role": describe_session_role(viewer, session_record),
        "session_username": viewer.username,
        "session_avatar_url": _get_account_avatar(db, viewer.id),
        "templates": prepared_templates,
        "delivery_modes": delivery_modes,
        "interval_options": interval_options,
    }
    return templates.TemplateResponse("requests/recurring.html", context)


@router.post("/requests/recurring")
def create_recurring_template(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    *,
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[str, Form(...)],
    contact_email_override: Annotated[Optional[str], Form()] = None,
    delivery_mode: Annotated[str, Form()] = RecurringRequestDeliveryMode.draft.value,
    interval_preset: Annotated[Optional[str], Form()] = None,
    custom_interval_value: Annotated[Optional[int], Form()] = None,
    custom_interval_unit: Annotated[Optional[str], Form()] = "days",
    next_run_at: Annotated[Optional[str], Form()] = None,
):
    delivery = _parse_delivery_mode(delivery_mode)
    next_run = _parse_datetime_local(next_run_at)
    interval_minutes = _resolve_interval_minutes(
        interval_preset,
        custom_interval_value,
        custom_interval_unit,
    )
    recurring_template_service.create_template(
        db,
        user_id=session_user.user.id,
        title=title,
        description=description,
        contact_email_override=contact_email_override,
        delivery_mode=delivery,
        interval_minutes=interval_minutes,
        next_run_at=next_run,
    )
    return RedirectResponse(url="/requests/recurring", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/recurring/{template_id}/action")
def recurring_template_action(
    template_id: int,
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    *,
    action: Annotated[str, Form(...)],
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    contact_email_override: Annotated[Optional[str], Form()] = None,
    delivery_mode: Annotated[Optional[str], Form()] = None,
    interval_preset: Annotated[Optional[str], Form()] = None,
    custom_interval_value: Annotated[Optional[int], Form()] = None,
    custom_interval_unit: Annotated[Optional[str], Form()] = None,
    next_run_at: Annotated[Optional[str], Form()] = None,
):
    template = recurring_template_service.get_template_for_user(
        db,
        template_id=template_id,
        user_id=session_user.user.id,
    )
    action_value = action.lower().strip()
    if action_value == "delete":
        recurring_template_service.delete_template(db, template=template)
    elif action_value == "pause":
        recurring_template_service.update_template(db, template=template, paused=True)
    elif action_value == "resume":
        recurring_template_service.update_template(db, template=template, paused=False)
    elif action_value == "edit":
        mode = _parse_delivery_mode(delivery_mode) if delivery_mode else None
        next_run = _parse_datetime_local(next_run_at)
        resolved_interval = None
        if interval_preset or custom_interval_value is not None:
            resolved_interval = _resolve_interval_minutes(
                interval_preset,
                custom_interval_value,
                custom_interval_unit,
            )
        recurring_template_service.update_template(
            db,
            template=template,
            title=title,
            description=description,
            contact_email_override=contact_email_override,
            delivery_mode=mode,
            interval_minutes=resolved_interval,
            next_run_at=next_run,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown action")
    return RedirectResponse(url="/requests/recurring", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/complete")
def complete_request(
    request_id: int,
    request: Request,
    db: SessionDep,
    user: User = Depends(require_authenticated_user),
):
    request_services.mark_completed(db, request_id=request_id, user=user)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/pin")
def pin_request(
    request_id: int,
    request: Request,
    db: SessionDep,
    user: User = Depends(require_admin),
    rank: Annotated[Optional[int], Form()] = None,
    next: Annotated[Optional[str], Form()] = None,
):
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    already_pinned = request_pin_service.request_is_pinned(db, request_id=request_id)
    if not already_pinned:
        request_pin_service.ensure_capacity(db)
        request_pin_service.set_pin(db, request=help_request, actor=user, rank=rank)
    elif rank is not None:
        request_pin_service.update_pin_rank(db, request_id=request_id, new_rank=rank)
    return _redirect_back(request, next)


@router.post("/requests/{request_id}/unpin")
def unpin_request(
    request_id: int,
    request: Request,
    db: SessionDep,
    user: User = Depends(require_admin),
    next: Annotated[Optional[str], Form()] = None,
):
    # Ensure request exists even if attribute missing
    request_services.get_request_by_id(db, request_id=request_id)
    request_pin_service.clear_pin(db, request_id=request_id)
    return _redirect_back(request, next)


@router.post("/requests/{request_id}/pin/reorder")
def reorder_pinned_request(
    request_id: int,
    request: Request,
    direction: Annotated[str, Form()],
    db: SessionDep,
    user: User = Depends(require_admin),
    next: Annotated[Optional[str], Form()] = None,
):
    direction_value = direction.lower()
    if direction_value not in {"up", "down"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid direction")
    request_services.get_request_by_id(db, request_id=request_id)
    literal_direction = cast(Literal["up", "down"], direction_value)
    request_pin_service.shift_pin(db, request_id=request_id, direction=literal_direction)
    return _redirect_back(request, next)



@router.get("/requests/{request_id}")
def request_detail(
    request: Request,
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    page: int = Query(1, ge=1),
    chat_q: str = Query("", alias="chat_q"),
    chat_topic: list[str] | None = Query(None, alias="chat_topic"),
    chat_participant: list[int] | None = Query(None, alias="chat_participant"),
) -> Response:
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    chat_filters = {
        "query": (chat_q or "").strip(),
        "topics": [value.strip().lower() for value in (chat_topic or []) if value and value.strip()],
        "participants": [pid for pid in (chat_participant or []) if pid],
    }
    context = _build_request_detail_context(
        request,
        db,
        session_user,
        help_request,
        page=page,
        chat_search_filters=chat_filters,
    )
    return templates.TemplateResponse("requests/detail.html", context)


@router.get("/requests/{request_id}/chat-search")
def request_chat_search(
    request_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    q: str = Query("", max_length=200),
    participant_id: list[int] | None = Query(None, alias="participant"),
    topic: list[str] | None = Query(None),
    limit: int = Query(request_chat_search_service.DEFAULT_RESULT_LIMIT, ge=1, le=100),
) -> Response:
    help_request = request_services.get_request_by_id(db, request_id=request_id)
    query = (q or "").strip()
    participant_ids = [pid for pid in (participant_id or []) if pid]
    topic_filters = [value.strip().lower() for value in (topic or []) if value and value.strip()]

    index, matches = request_chat_search_service.search_chat(
        db,
        help_request.id,
        query=query,
        participant_ids=participant_ids,
        topics=topic_filters,
        limit=limit,
    )
    attr_key = _signal_display_attr_key(help_request)
    display_names = _load_signal_display_names_for_user_ids(
        db,
        {result.user_id for result in matches},
        attr_key,
    )

    payload = {
        "request_id": help_request.id,
        "query": query,
        "results": [
            {
                **request_chat_search_service.serialize_result(result),
                "display_name": display_names.get(result.user_id),
                "comment_anchor": result.anchor,
            }
            for result in matches
        ],
        "meta": {
            "generated_at": index.generated_at,
            "total_entries": index.entry_count,
            "participants": index.participants,
            "limit": limit,
        },
        "display_names": {str(user_id): name for user_id, name in display_names.items()},
    }
    return JSONResponse(payload)


@router.get("/comments/{comment_id}")
def comment_detail(
    request: Request,
    comment_id: int,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    viewer = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(viewer, session_record)

    comment = db.get(RequestComment, comment_id)
    if not comment or comment.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    help_request = db.get(HelpRequest, comment.help_request_id)
    if not help_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    is_restricted = help_request.status in {"pending", HELP_REQUEST_STATUS_DRAFT}
    if is_restricted and not (
        viewer.is_admin or help_request.created_by_user_id == viewer.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    author = db.get(User, comment.user_id)
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    attr_key = _signal_display_attr_key(help_request)
    display_name_map = _load_signal_display_names_for_user_ids(db, {author.id}, attr_key)
    display_name = display_name_map.get(author.id)

    serialized_comment = request_comment_service.serialize_comment(
        comment,
        author,
        display_name=display_name,
    )

    serialized_request = _serialize_requests(db, [help_request], viewer=viewer)
    request_payload = serialized_request[0] if serialized_request else None
    comment_insight = comment_llm_insights_service.get_analysis_by_comment_id(comment.id)

    context = {
        "request": request,
        "user": viewer,
        "session": session_record,
        "session_role": session_role,
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "comment": serialized_comment,
        "comment_author": author,
        "comment_display_name": display_name,
        "request_summary": request_payload,
        "comment_insight": comment_insight,
    }
    return templates.TemplateResponse("comments/detail.html", context)


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

    try:
        request_chat_search_service.refresh_chat_index(db, help_request.id)
    except Exception:  # pragma: no cover - best-effort cache update
        logger.warning("Failed to refresh chat search index for request %s", help_request.id, exc_info=True)

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
    caption_prefs = load_caption_preferences(db, session_user.user.id)
    context = {
        "request": request,
        "inviter_username": session_user.user.username,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "session_avatar_url": session_user.avatar_url,
        "invite_caption": build_caption_payload(
            caption_prefs,
            caption_id="invite_intro",
            text="Make the invite personal so your friend lands with a smile and knows how you plan to support them.",
        ),
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

    hide_captions = caption_preference_service.get_global_hidden(db, user.id)
    if form_values is None:
        form_values = {
            "contact_email": user.contact_email or "",
            "hide_helper_captions": "1" if hide_captions else "",
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
        "hide_helper_captions": hide_captions,
    }


def _build_rss_feed_url(request: Request, token_value: str, category_slug: str) -> str:
    base = get_base_url(request)
    return f"{base}/feeds/{token_value}/{category_slug}.xml"


def _load_rss_feed_entries(
    request: Request,
    db: Session,
    user: User,
    *,
    allowed_slugs: Optional[Sequence[str]] = None,
) -> list[dict[str, object]]:
    variants = rss_feed_catalog.list_variants_for_user(user)
    allowed = set(allowed_slugs or [])
    entries: list[dict[str, object]] = []
    for variant in variants:
        if allowed and variant.slug not in allowed:
            continue
        token = rss_feed_token_service.get_or_create_token(
            db,
            user_id=user.id,
            category=variant.slug,
        )
        entries.append(
            {
                "variant": variant,
                "token": token,
                "url": _build_rss_feed_url(request, token.token, variant.slug),
            }
        )
    return entries


def _build_rss_link_metadata(entries: list[dict[str, object]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for entry in entries:
        variant = entry["variant"]
        url = entry["url"]
        links.append(
            {
                "title": f"WhiteBalloon – {variant.label}",
                "href": url,
            }
        )
    return links


def _build_rss_settings_context(
    request: Request,
    db: Session,
    session_user: SessionUser,
    *,
    form_message: Optional[str] = None,
    form_status: Optional[str] = None,
) -> dict[str, object]:
    user = session_user.user
    session_record = session_user.session
    session_role = describe_session_role(user, session_record)
    session_avatar_url = _get_account_avatar(db, user.id)
    feed_entries = _load_rss_feed_entries(request, db, user)
    return {
        "request": request,
        "user": user,
        "session": session_record,
        "session_role": session_role,
        "session_username": user.username,
        "session_avatar_url": session_avatar_url,
        "rss_feeds": feed_entries,
        "rss_feed_links": _build_rss_link_metadata(feed_entries),
        "form_message": form_message,
        "form_status": form_status,
    }


def _build_request_detail_context(
    request: Request,
    db: Session,
    session_user: SessionUser,
    help_request: HelpRequest,
    *,
    comment_form_errors: Optional[list[str]] = None,
    comment_form_body: str = "",
    page: int = 1,
    recent_limit: Optional[int] = None,
    chat_search_filters: Optional[dict[str, object]] = None,
) -> dict[str, object]:
    viewer = session_user.user
    session_record = session_user.session

    if help_request.status == "pending" and not (
        viewer.is_admin or help_request.created_by_user_id == viewer.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    creator_usernames = request_services.load_creator_usernames(db, [help_request])
    attr_key = _signal_display_attr_key(help_request)
    creator_display_name = _map_request_creator_display_names(db, [help_request]).get(help_request.id)
    pin_map = request_pin_service.get_pin_map(db)
    pin_meta = pin_map.get(help_request.id)
    serialized = RequestResponse.from_model(
        help_request,
        created_by_username=creator_usernames.get(help_request.created_by_user_id),
        created_by_display_name=creator_display_name,
        can_complete=calculate_can_complete(help_request, viewer),
        is_pinned=pin_meta is not None,
        pin_rank=pin_meta.rank if pin_meta else None,
    )

    readonly = not session_record.is_fully_authenticated
    session_role = describe_session_role(viewer, session_record)

    # Pagination
    comments_per_page = request_comment_service.DEFAULT_COMMENTS_PER_PAGE
    active_insight_filters = _parse_insight_filters(request)
    filters_active = _insight_filters_active(active_insight_filters)
    if filters_active:
        offset = 0
        limit = None
        comment_rows, total_comments = request_comment_service.list_comments(
            db,
            help_request_id=help_request.id,
            limit=limit,
            offset=offset,
        )
    elif recent_limit:
        comment_rows, total_comments = request_comment_service.list_recent_comments(
            db,
            help_request_id=help_request.id,
            limit=recent_limit,
        )
    else:
        offset = (page - 1) * comments_per_page
        limit = comments_per_page
        comment_rows, total_comments = request_comment_service.list_comments(
            db,
            help_request_id=help_request.id,
            limit=limit,
            offset=offset,
        )
    display_names = _load_signal_display_names(db, comment_rows, attr_key)
    insights_lookup = _build_comment_insights_lookup(help_request.id)
    matching_comment_ids: set[int] | None = None
    if filters_active:
        matching_comment_ids = {
            comment_id
            for comment_id, metadata in insights_lookup.items()
            if _insight_metadata_matches(metadata, active_insight_filters)
        }
        if matching_comment_ids:
            stmt = (
                select(RequestComment, User)
                .join(User, User.id == RequestComment.user_id)
                .where(RequestComment.id.in_(matching_comment_ids))
                .order_by(RequestComment.created_at.desc())
            )
            comment_rows = list(db.exec(stmt).all())
            total_comments = len(comment_rows)
        else:
            comment_rows = []
            total_comments = 0
    comments = []
    visible_count = 0
    for comment, author in comment_rows:
        serialized_comment = request_comment_service.serialize_comment(
            comment,
            author,
            display_name=display_names.get(author.id),
        )
        body_text = serialized_comment.get("body") or ""
        clean_body, reactions = chat_reaction_parser.strip_reactions(body_text)
        serialized_comment["body"] = clean_body
        serialized_comment["reaction_summary"] = [
            {"emoji": reaction.emoji, "count": reaction.count} for reaction in reactions
        ]
        metadata = insights_lookup.get(comment.id, {})
        serialized_comment["insight_metadata"] = metadata
        matches_filters = not filters_active or _matches_insight_filters(
            serialized_comment,
            active_insight_filters,
        )
        serialized_comment["matches_insight_filters"] = matches_filters
        if matches_filters:
            visible_count += 1
            serialized_comment.pop("hidden_via_insight", None)
        else:
            serialized_comment["hidden_via_insight"] = True
        comments.append(serialized_comment)
    comment_promotions = comment_request_promotion_service.get_promotions_for_comment_ids(
        db, [item["id"] for item in comments]
    )
    settings = config.get_settings()
    show_comment_insights = settings.comment_insights_indicator_enabled and viewer.is_admin
    comment_insights_map: dict[int, dict[str, object]] = {}
    promoted_comment_context: Optional[dict[str, object]] = None
    promotion = db.exec(
        select(CommentPromotion).where(CommentPromotion.request_id == help_request.id)
    ).first()
    if promotion:
        source_comment = db.get(RequestComment, promotion.comment_id)
        if source_comment:
            source_author = db.get(User, source_comment.user_id)
            if source_author:
                insight = comment_llm_insights_service.get_analysis_by_comment_id(source_comment.id)
                display_name_map = _load_signal_display_names_for_user_ids(
                    db,
                    {source_author.id},
                    attr_key,
                )
                promoted_comment_context = {
                    "comment": request_comment_service.serialize_comment(
                        source_comment,
                        source_author,
                        display_name=display_name_map.get(source_author.id),
                    ),
                    "insight": insight,
                    "promotion": promotion,
                }

    if show_comment_insights:
        for item in comments:
            analysis = comment_llm_insights_service.get_analysis_by_comment_id(item["id"])
            if analysis:
                page = request_comment_service.get_comment_page(
                    db,
                    help_request_id=analysis.help_request_id,
                    comment_id=analysis.comment_id,
                )
                comment_insights_map[item["id"]] = {
                    "summary": analysis.summary,
                    "resource_tags": analysis.resource_tags,
                    "request_tags": analysis.request_tags,
                    "audience": analysis.audience,
                    "residency_stage": analysis.residency_stage,
                    "location": analysis.location,
                    "location_precision": analysis.location_precision,
                    "urgency": analysis.urgency,
                    "sentiment": analysis.sentiment,
                    "tags": analysis.tags,
                    "notes": analysis.notes,
                    "run_id": analysis.run_id,
                    "recorded_at": analysis.recorded_at,
                    "page": page,
                }
    can_moderate = viewer.is_admin
    can_toggle_sync_scope = viewer.is_admin

    # Calculate pagination info
    comment_total_count = total_comments
    comment_visible_count = visible_count if filters_active else len(comments)
    effective_page_size = recent_limit if (recent_limit and not filters_active) else comments_per_page
    if filters_active:
        total_pages = 1
        current_page = 1
    else:
        page_size = effective_page_size or comments_per_page or 1
        total_pages = max(1, (total_comments + page_size - 1) // page_size) if total_comments else 1
        if recent_limit:
            current_page = total_pages
        else:
            current_page = min(page, total_pages) if total_pages else 1
    
    def _page_url(target_page: int) -> str:
        url = request.url.include_query_params(page=target_page)
        return str(url)
    
    pagination = {
        "has_prev": False if filters_active else current_page > 1,
        "has_next": False if filters_active else current_page < total_pages,
        "prev_url": None if filters_active else (_page_url(current_page - 1) if current_page > 1 else None),
        "next_url": None if filters_active else (_page_url(current_page + 1) if current_page < total_pages else None),
        "current_page": 1 if filters_active else current_page,
        "total_pages": 1 if filters_active else total_pages,
        "total_comments": comment_total_count,
    }

    show_chat_search_panel = total_comments >= CHAT_SEARCH_MIN_COMMENTS

    chat_filters = chat_search_filters or {}
    chat_query = str(chat_filters.get("query", "") or "").strip()
    participant_filters = [int(pid) for pid in chat_filters.get("participants", []) if pid]
    topic_filters = [str(topic) for topic in chat_filters.get("topics", []) if topic]
    chat_results: list[dict[str, object]] = []
    chat_meta: dict[str, object] | None = None
    related_chats: list[dict[str, object]] = []
    if chat_query or participant_filters or topic_filters:
        index, matches = request_chat_search_service.search_chat(
            db,
            help_request.id,
            query=chat_query,
            participant_ids=participant_filters,
            topics=topic_filters,
        )
        display_names_map = _load_signal_display_names_for_user_ids(
            db,
            {match.user_id for match in matches},
            attr_key,
        )
        chat_results = [
            {
                **request_chat_search_service.serialize_result(match),
                "display_name": display_names_map.get(match.user_id)
                or display_names.get(match.user_id),
            }
            for match in matches
        ]
        chat_meta = {
            "generated_at": index.generated_at,
            "total_entries": index.entry_count,
            "limit": request_chat_search_service.DEFAULT_RESULT_LIMIT,
        }
    else:
        related_chats = request_chat_suggestions.suggest_related_requests(db, help_request.id)

    comment_insights_summary = _build_request_comment_insights_summary(help_request.id)
    comment_visible_count = visible_count if filters_active else len(comments)
    comment_total_count = comment_visible_count if filters_active else total_comments

    insight_reset_url = request.url
    for param in ("insight_resource", "insight_request", "insight_urgency", "insight_sentiment"):
        insight_reset_url = insight_reset_url.remove_query_params(param)

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
        "can_promote_comments": session_record.is_fully_authenticated,
        "can_moderate_comments": can_moderate,
        "can_toggle_sync_scope": can_toggle_sync_scope,
        "comment_form_errors": comment_form_errors or [],
        "comment_form_body": comment_form_body,
        "comment_max_length": request_comment_service.MAX_COMMENT_LENGTH,
        "request_id": help_request.id,
        "comment_display_names": display_names,
        "comment_promotions": comment_promotions,
        "insight_filters": active_insight_filters,
        "insight_filters_active": filters_active,
        "comment_visible_count": comment_visible_count,
        "comment_total_count": comment_total_count,
        "pagination": pagination,
        "show_chat_search_panel": show_chat_search_panel,
        "chat_search": {
            "query": chat_query,
            "participants": participant_filters,
            "topics": topic_filters,
            "results": chat_results,
            "meta": chat_meta,
            "has_query": bool(chat_query or participant_filters or topic_filters),
        },
        "related_chat_suggestions": related_chats,
        "comment_insights_enabled": show_comment_insights,
        "comment_insights_map": comment_insights_map,
        "comment_insights_summary": comment_insights_summary,
        "promoted_comment_context": promoted_comment_context,
        "can_pin_requests": viewer.is_admin,
        "insight_reset_url": str(insight_reset_url),
    }


_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    return _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")


def _signal_display_attr_key(help_request: HelpRequest) -> Optional[str]:
    title = (help_request.title or "").strip()
    if not title.startswith("[Signal]"):
        return None
    _, _, group_name = title.partition("]")
    group_name = group_name.strip()
    if not group_name:
        return None
    slug = _slugify(group_name)
    if not slug:
        return None
    return f"signal_display_name:{slug}"


def _load_signal_display_names(
    db: Session,
    comment_rows: list[tuple[RequestComment, User]],
    attr_key: Optional[str],
) -> dict[int, str]:
    user_ids = {author.id for _, author in comment_rows}
    return _load_signal_display_names_for_user_ids(db, user_ids, attr_key)


def _load_signal_display_names_for_user_ids(
    db: Session,
    user_ids: set[int],
    attr_key: Optional[str],
) -> dict[int, str]:
    if not attr_key or not user_ids:
        return {}
    rows = db.exec(
        select(UserAttribute.user_id, UserAttribute.value)
        .where(UserAttribute.user_id.in_(user_ids))
        .where(UserAttribute.key == attr_key)
    ).all()
    return {user_id: value for user_id, value in rows if value}


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


@router.get("/settings/notifications")
def settings_notifications(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    context = _build_rss_settings_context(request, db, session_user)
    return templates.TemplateResponse("settings/notifications.html", context)


@router.post("/settings/notifications/rotate")
def settings_notifications_rotate(
    request: Request,
    category: Annotated[str, Form()],
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    variant = rss_feed_catalog.get_variant(category)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    if variant.require_admin and not session_user.user.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    rss_feed_token_service.rotate_token(
        db,
        user_id=session_user.user.id,
        category=variant.slug,
    )
    context = _build_rss_settings_context(
        request,
        db,
        session_user,
        form_message=f"{variant.label} feed URL regenerated.",
        form_status="success",
    )
    return templates.TemplateResponse("settings/notifications.html", context)


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
    hide_helper_captions: Annotated[Optional[str], Form()] = None,
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

    caption_preference_service.set_global_hidden(
        db,
        user_id=user.id,
        hidden=bool(hide_helper_captions),
        actor_user_id=user.id,
    )

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

    form_values = {
        "contact_email": user.contact_email or "",
        "hide_helper_captions": "1" if caption_preference_service.get_global_hidden(db, user.id) else "",
    }
    context = _build_account_settings_context(
        request,
        db,
        session_user,
        form_values=form_values,
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

    recent_comments: list[dict[str, object]] = []
    show_recent_comments = viewer.is_admin
    if show_recent_comments:
        rows = request_comment_service.list_recent_comments_for_user(db, person.id)
        for comment, help_request in rows:
            created_at_iso = comment.created_at.isoformat() if comment.created_at else None
            recent_comments.append(
                {
                    "id": comment.id,
                    "body": comment.body,
                    "created_at": comment.created_at,
                    "created_at_iso": created_at_iso,
                    "request_id": help_request.id,
                    "request_title": help_request.title or f"Request #{help_request.id}",
                    "request_url": f"/requests/{help_request.id}",
                    "scope": (comment.sync_scope or "private").title(),
                }
            )

    settings = config.get_settings()
    highlight = None
    highlight_receipts: list[dict[str, object]] = []
    snapshot_links: list[dict[str, object]] = []
    snapshot_request_ctas: list[dict[str, object]] = []
    if settings.profile_signal_glaze_enabled:
        highlight = user_profile_highlight_service.get(db, person.id)
        if highlight:
            highlight_receipts = _format_proof_receipts(highlight.proof_points)
        snapshot = signal_profile_snapshot_service.build_snapshot(
            db,
            person.id,
            group_slug=highlight.source_group if highlight and highlight.source_group else None,
        )
        if snapshot:
            snapshot_links = _format_snapshot_links(snapshot.top_links)
            snapshot_request_ctas = _build_request_ctas(snapshot.request_ids, person.id)

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
        "show_recent_comments": show_recent_comments,
        "recent_comments": recent_comments,
        "recent_comments_limit": request_comment_service.RECENT_PROFILE_COMMENTS_LIMIT,
        "recent_comments_url": f"/people/{person.username}/comments",
        "profile_glaze_enabled": settings.profile_signal_glaze_enabled,
        "profile_highlight": highlight,
        "profile_highlight_receipts": highlight_receipts,
        "profile_snapshot_links": snapshot_links,
        "profile_request_ctas": snapshot_request_ctas,
    }
    return templates.TemplateResponse("profile/show.html", context)


@router.post("/api/metrics")
async def ingest_metric(
    request: Request,
    session_user: SessionUser = Depends(require_session_user),
):
    try:
        payload = await request.json()
    except Exception:  # pragma: no cover - malformed bodies
        raise HTTPException(status_code=400, detail="Invalid payload")

    category = str(payload.get("category", "")).strip().lower()
    event = str(payload.get("event", "")).strip().lower()
    if not category or not event:
        raise HTTPException(status_code=400, detail="category and event required")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    sanitized_metadata = {str(key): str(value) for key, value in metadata.items()}
    subject_id = payload.get("subject_id")
    logger.info(
        "metric_event",
        extra={
            "category": category,
            "event": event,
            "viewer_id": session_user.user.id,
            "subject_id": subject_id,
            "metadata": sanitized_metadata,
        },
    )
    return JSONResponse({"ok": True})


@router.get("/people/{username}/comments")
def profile_comments(
    username: str,
    request: Request,
    db: SessionDep,
    page: int = Query(1, ge=1),
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    viewer = session_user.user
    if not viewer.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    normalized = auth_service.normalize_username(username)
    person = db.exec(select(User).where(User.username == normalized)).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows, total_count = request_comment_service.paginate_comments_for_user(
        db,
        person.id,
        page=page,
    )
    comment_groups: list[dict[str, object]] = []
    for comment, help_request in rows:
        created_at_iso = comment.created_at.isoformat() if comment.created_at else None
        title = help_request.title or f"Request #{help_request.id}"
        group_url = f"/requests/{help_request.id}"
        if not comment_groups or comment_groups[-1]["request_id"] != help_request.id:
            comment_groups.append(
                {
                    "request_id": help_request.id,
                    "request_title": title,
                    "request_url": group_url,
                    "comments": [],
                }
            )
        comment_groups[-1]["comments"].append(
            {
                "id": comment.id,
                "body": comment.body,
                "created_at": comment.created_at,
                "created_at_iso": created_at_iso,
                "scope": (comment.sync_scope or "private").title(),
                "comment_url": f"/comments/{comment.id}",
                "username": person.username,
                "display_name": person.username,
            }
        )

    per_page = request_comment_service.PROFILE_COMMENTS_PER_PAGE
    total_pages = max(1, (total_count + per_page - 1) // per_page) if per_page else 1
    current_page = min(page, total_pages)

    def _page_url(target_page: int) -> str:
        return str(request.url.include_query_params(page=target_page))

    pagination = {
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_url": _page_url(current_page - 1) if current_page > 1 else None,
        "next_url": _page_url(current_page + 1) if current_page < total_pages else None,
        "current_page": current_page,
        "total_pages": total_pages,
        "total_comments": total_count,
    }

    viewer_session = session_user.session
    context = {
        "request": request,
        "person": person,
        "comment_groups": comment_groups,
        "pagination": pagination,
        "user": viewer,
        "session": viewer_session,
        "session_role": describe_session_role(viewer, viewer_session),
        "session_username": viewer.username,
        "session_avatar_url": session_user.avatar_url,
        "profile_url": f"/people/{person.username}",
    }
    return templates.TemplateResponse("profile/comments.html", context)


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


def _parse_delivery_mode(value: str | None) -> RecurringRequestDeliveryMode:
    if not value:
        return RecurringRequestDeliveryMode.draft
    try:
        return RecurringRequestDeliveryMode(value)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid delivery mode") from error


def _parse_datetime_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date/time") from error


def _resolve_interval_minutes(
    interval_preset: str | None,
    custom_value: int | None,
    custom_unit: str | None,
) -> int:
    if interval_preset:
        try:
            minutes = int(interval_preset)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid interval preset") from error
        if minutes <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")
        return minutes

    if not custom_value or custom_value <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Custom interval must be positive")
    unit = (custom_unit or "minutes").lower()
    unit_map = {
        "minutes": 1,
        "hours": 60,
        "days": 1440,
        "weeks": 10080,
    }
    if unit not in unit_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid interval unit")
    minutes = custom_value * unit_map[unit]
    if minutes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")
    return minutes


def _recurring_interval_options() -> list[dict[str, str]]:
    return [
        {"value": "1440", "label": "Daily"},
        {"value": "2880", "label": "Every 2 days"},
        {"value": "10080", "label": "Weekly"},
        {"value": "20160", "label": "Every 2 weeks"},
    ]


def _match_interval_preset(minutes: int) -> str | None:
    for option in _recurring_interval_options():
        if minutes == int(option["value"]):
            return option["value"]
    return None


def _minutes_to_custom_interval(minutes: int) -> tuple[int, str]:
    for unit, factor in (("weeks", 10080), ("days", 1440), ("hours", 60)):
        if minutes % factor == 0:
            return minutes // factor, unit
    return minutes, "minutes"


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


def _get_account_avatar(db: Session, user_id: int) -> Optional[str]:
    return user_attribute_service.get_attribute(
        db,
        user_id=user_id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )


from . import admin as admin_routes
from . import members as members_routes
from . import menu as menu_routes
from . import peer_auth as peer_auth_routes
from . import sessions as session_routes
from . import sync as sync_routes


router.include_router(session_routes.router)
router.include_router(sync_routes.router)
router.include_router(members_routes.router)
router.include_router(menu_routes.router)
router.include_router(peer_auth_routes.router)
router.include_router(admin_routes.router)
