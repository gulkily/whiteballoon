from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from urllib.parse import urlparse

from sqlmodel import Session, select

from app.models import HelpRequest, RequestComment, UserAttribute
from app.services import comment_llm_insights_service
from app.services.signal_profile_snapshot import LinkStat, SignalProfileSnapshot, TagStat

_URL_PATTERN = re.compile(r"https?://[\w./?=&%#\-]+", re.IGNORECASE)
_ATTACHMENT_PATTERN = re.compile(r"^\[attachments:\s*(?P<files>.+)\]$", re.IGNORECASE)
_REACTIONS_PATTERN = re.compile(r"^\(Reactions:\s*(?P<entries>.+)\)$", re.IGNORECASE)
_MAX_LINKS = 5
_MAX_TAGS = 5


@dataclass
class SignalGroupMembership:
    slug: str
    name: str


def build_snapshot(
    session: Session,
    user_id: int,
    *,
    group_slug: str | None = None,
) -> SignalProfileSnapshot | None:
    membership = _resolve_group_membership(session, user_id, group_slug)
    if not membership:
        return None

    request_ids = _load_request_ids(session, membership.name)
    if not request_ids:
        return None

    comments = _load_comments(session, user_id, request_ids)
    if not comments:
        return None

    message_count = len(comments)
    first_seen = comments[0].created_at
    last_seen = comments[-1].created_at

    link_stats = _build_link_stats(comment.body for comment in comments)
    tag_stats = _build_tag_stats(comment.id for comment in comments)
    reaction_counts = _collect_reaction_counts(comment.body for comment in comments)
    attachment_counts = _collect_attachment_counts(comment.body for comment in comments)

    return SignalProfileSnapshot(
        user_id=user_id,
        group_slug=membership.slug,
        message_count=message_count,
        first_seen_at=first_seen,
        last_seen_at=last_seen,
        top_links=link_stats,
        top_tags=tag_stats,
        reaction_counts=reaction_counts,
        attachment_counts=attachment_counts,
        request_ids=sorted({comment.help_request_id for comment in comments}),
    )


def _resolve_group_membership(
    session: Session, user_id: int, group_slug: str | None
) -> SignalGroupMembership | None:
    stmt = select(UserAttribute.key, UserAttribute.value).where(
        UserAttribute.user_id == user_id,
        UserAttribute.key.like("signal_import_group:%"),
    )
    rows = session.exec(stmt).all()
    memberships = []
    for key, value in rows:
        slug = key.split(":", 1)[1] if ":" in key else key
        memberships.append(SignalGroupMembership(slug=slug, name=value or slug))
    if not memberships:
        return None
    if group_slug:
        for membership in memberships:
            if membership.slug == group_slug:
                return membership
        return None
    return memberships[0]


def _load_request_ids(session: Session, group_name: str) -> list[int]:
    title = f"[Signal] {group_name}".strip()
    stmt = select(HelpRequest.id).where(HelpRequest.title == title)
    return list(session.exec(stmt).all())


def _load_comments(session: Session, user_id: int, request_ids: list[int]) -> list[RequestComment]:
    if not request_ids:
        return []
    stmt = (
        select(RequestComment)
        .where(
            RequestComment.user_id == user_id,
            RequestComment.help_request_id.in_(request_ids),
        )
        .order_by(RequestComment.created_at.asc(), RequestComment.id.asc())
    )
    return list(session.exec(stmt).all())


def _build_link_stats(bodies: Iterable[str]) -> list[LinkStat]:
    counter: Counter[str] = Counter()
    for body in bodies:
        for match in _URL_PATTERN.findall(body or ""):
            counter[_normalize_url(match)] += 1
    stats = []
    for url, count in counter.most_common(_MAX_LINKS):
        domain = urlparse(url).netloc.lower()
        stats.append(LinkStat(url=url, domain=domain, count=count))
    return stats


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{scheme}://{netloc}{path}{query}"


def _build_tag_stats(comment_ids: Iterable[int]) -> list[TagStat]:
    tag_counter: Counter[str] = Counter()
    for comment_id in comment_ids:
        insight = comment_llm_insights_service.get_analysis_by_comment_id(comment_id)
        if not insight:
            continue
        tags = insight.resource_tags + insight.request_tags + insight.tags
        for tag in tags:
            tag_counter[tag] += 1
    return [
        TagStat(label=label, count=count)
        for label, count in tag_counter.most_common(_MAX_TAGS)
    ]


def _collect_reaction_counts(bodies: Iterable[str]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for body in bodies:
        for line in body.splitlines():
            match = _REACTIONS_PATTERN.match(line.strip())
            if not match:
                continue
            entries = match.group("entries").split(",")
            for entry in entries:
                emoji = entry.strip().split(" ")[-1]
                if emoji:
                    counter[emoji] += 1
    return dict(counter)


def _collect_attachment_counts(bodies: Iterable[str]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for body in bodies:
        for line in body.splitlines():
            match = _ATTACHMENT_PATTERN.match(line.strip())
            if not match:
                continue
            files = [part.strip() for part in match.group("files").split(",") if part.strip()]
            for filename in files:
                counter[_infer_attachment_type(filename)] += 1
    return dict(counter)


def _infer_attachment_type(filename: str) -> str:
    lowered = filename.lower()
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        if lowered.endswith(ext):
            return "image"
    if lowered.endswith((".mp4", ".mov", ".avi")):
        return "video"
    if lowered.endswith((".pdf", ".doc", ".docx")):
        return "document"
    return "other"
