from __future__ import annotations

from datetime import datetime, timezone
import html
from email.utils import format_datetime
from xml.etree import ElementTree as ET

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.dependencies import SessionDep
from app.models import User
from app.modules.requests import services as request_services
from app.modules.requests.routes import RequestResponse, calculate_can_complete
from app.services import recurring_template_service, request_pin_service, rss_feed_catalog, rss_feed_token_service
from app.url_utils import get_base_url


router = APIRouter(prefix="/feeds", tags=["feeds"])


def _format_rfc2822(value: str | datetime | None) -> str:
    if value is None:
        return format_datetime(datetime.utcnow().replace(tzinfo=timezone.utc))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return format_datetime(datetime.utcnow().replace(tzinfo=timezone.utc))
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    else:
        dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt.astimezone(timezone.utc))


def _request_title(payload: RequestResponse) -> str:
    description = (payload.description or "").strip()
    if payload.status == "pending":
        prefix = "[Pending] "
    elif payload.status == "completed":
        prefix = "[Completed] "
    else:
        prefix = ""
    base_title = description.splitlines()[0] if description else ""
    if not base_title:
        base_title = f"Request #{payload.id}"
    return f"{prefix}{base_title[:160]}"


def _normalize_description(payload: RequestResponse) -> str:
    summary = (payload.description or "").strip()
    author = payload.created_by_username or "Anonymous"
    lines = [
        f"Status: {payload.status}",
        f"Author: @{author}",
    ]
    if summary:
        lines.extend(["", summary])
    body = "\n".join(line for line in lines if line is not None)
    escaped = html.escape(body).replace("\n", "<br />\n")
    return f"<div>{escaped}</div>"


def _set_cdata(element: ET.Element, content: str) -> None:
    cdata = getattr(ET, "CDATA", None)
    if cdata:
        element.text = cdata(content)
    else:
        element.text = content


def _build_feed_document(
    *,
    title: str,
    link: str,
    description: str,
    items: list[RequestResponse],
) -> bytes:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = link
    ET.SubElement(channel, "description").text = description
    ET.SubElement(channel, "lastBuildDate").text = _format_rfc2822(datetime.utcnow().replace(tzinfo=timezone.utc))

    for item in items:
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = _request_title(item)
        ET.SubElement(entry, "link").text = f"{link}/requests/{item.id}"
        ET.SubElement(entry, "guid", isPermaLink="false").text = f"request-{item.id}"
        ET.SubElement(entry, "pubDate").text = _format_rfc2822(item.updated_at)
        description = ET.SubElement(entry, "description")
        _set_cdata(description, _normalize_description(item))
        if item.status:
            category = ET.SubElement(entry, "category")
            category.text = item.status

    return ET.tostring(rss, encoding="utf-8")


def _load_feed_payloads(
    db: SessionDep,
    *,
    variant_slug: str,
    viewer: User,
) -> list[RequestResponse]:
    variant = rss_feed_catalog.get_variant(variant_slug)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    if variant.require_admin and not viewer.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    filters = variant.build_query_kwargs(db, viewer)
    request_items = request_services.list_requests(db, **filters)
    pin_map = request_pin_service.get_pin_map(db)
    template_metadata = recurring_template_service.load_template_metadata(db, [req.id for req in request_items if req.id])
    creator_usernames = request_services.load_creator_usernames(db, request_items)
    serialized: list[RequestResponse] = []
    for help_request in request_items:
        template_info = template_metadata.get(help_request.id) if template_metadata else None
        serialized.append(
            RequestResponse.from_model(
                help_request,
                created_by_username=creator_usernames.get(help_request.created_by_user_id),
                can_complete=calculate_can_complete(help_request, viewer),
                is_pinned=help_request.id in pin_map,
                pin_rank=pin_map.get(help_request.id).rank if help_request.id in pin_map else None,
                recurring_template_id=template_info.get("template_id") if template_info else None,
                recurring_template_title=template_info.get("template_title") if template_info else None,
            )
        )
    return serialized


@router.get("/{token}/{category}.xml", response_class=Response)
def read_rss_feed(
    request: Request,
    token: str,
    category: str,
    db: SessionDep,
) -> Response:
    token_record = rss_feed_token_service.get_token_by_secret(db, token_value=token)
    if not token_record or token_record.category != category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    viewer = db.get(User, token_record.user_id)
    if not viewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    variant = rss_feed_catalog.get_variant(category)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    items = _load_feed_payloads(db, variant_slug=category, viewer=viewer)
    site_url = get_base_url(request)
    feed_title = f"WhiteBalloon – {variant.label}"
    feed_link = site_url.rstrip("/")
    body = _build_feed_document(
        title=feed_title,
        link=feed_link,
        description=variant.description,
        items=items,
    )
    rss_feed_token_service.record_access(db, token=token_record)
    return Response(content=body, media_type="application/rss+xml")
