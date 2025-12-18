from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import (
    HELP_REQUEST_STATUS_DRAFT,
    HelpRequest,
    RequestComment,
    User,
)


@dataclass
class ChatAIContextCitation:
    id: str
    label: str
    url: str
    snippet: str
    source_type: str


@dataclass
class ChatAIContextResult:
    prompt: str
    request_citations: list[ChatAIContextCitation] = field(default_factory=list)
    comment_citations: list[ChatAIContextCitation] = field(default_factory=list)
    guardrail: str | None = None

    @property
    def citations(self) -> list[ChatAIContextCitation]:
        return [*self.request_citations, *self.comment_citations]

    def is_empty(self) -> bool:
        return not self.request_citations and not self.comment_citations


def build_ai_chat_context(
    session: Session,
    *,
    prompt: str,
    user: User,
    context_scope: str = "auto",
    max_items: int = 5,
) -> ChatAIContextResult:
    """Aggregate citations for the AI chat response."""
    keywords = _extract_keywords(prompt)
    result = ChatAIContextResult(prompt=prompt)
    include_requests = context_scope in {"auto", "requests"}
    include_comments = context_scope in {"auto", "chats"}

    if include_requests:
        result.request_citations = list(_search_requests(session, keywords, user, limit=max_items))
    if include_comments:
        result.comment_citations = list(_search_comments(session, keywords, user, limit=max_items))

    if result.is_empty():
        result.guardrail = "No indexed requests or chats matched that question. Try different keywords or filters."
    return result


def _extract_keywords(prompt: str) -> list[str]:
    lowered = prompt.lower()
    tokens = re.findall(r"[a-z0-9]+", lowered)
    unique: list[str] = []
    for token in tokens:
        if len(token) < 3:
            continue
        if token in unique:
            continue
        unique.append(token)
    return unique


def _search_requests(
    session: Session,
    keywords: Sequence[str],
    user: User,
    *,
    limit: int,
) -> Iterable[ChatAIContextCitation]:
    stmt = (
        select(HelpRequest)
        .where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
        .order_by(HelpRequest.updated_at.desc())
    )
    if keywords:
        like_clauses = []
        for token in keywords:
            pattern = f"%{token}%"
            like_clauses.append(HelpRequest.title.ilike(pattern))
            like_clauses.append(HelpRequest.description.ilike(pattern))
        stmt = stmt.where(or_(*like_clauses))
    rows = session.exec(stmt.limit(limit * 3 if limit else 5)).all()
    results: list[ChatAIContextCitation] = []
    for request in rows:
        if not _request_visible(request, user):
            continue
        caption = request.title or f"Request #{request.id}"
        snippet = _trim_text(request.description or "")
        results.append(
            ChatAIContextCitation(
                id=f"request:{request.id}",
                label=caption,
                url=f"/requests/{request.id}",
                snippet=snippet,
                source_type="request",
            )
        )
        if len(results) >= limit:
            break
    return results


def _search_comments(
    session: Session,
    keywords: Sequence[str],
    user: User,
    *,
    limit: int,
) -> Iterable[ChatAIContextCitation]:
    stmt = (
        select(RequestComment, HelpRequest, User)
        .join(HelpRequest, HelpRequest.id == RequestComment.help_request_id)
        .join(User, User.id == RequestComment.user_id)
        .where(RequestComment.deleted_at.is_(None))
        .order_by(RequestComment.created_at.desc())
    )
    if keywords:
        like_clauses = []
        for token in keywords:
            pattern = f"%{token}%"
            like_clauses.append(RequestComment.body.ilike(pattern))
        if like_clauses:
            stmt = stmt.where(or_(*like_clauses))
    rows = session.exec(stmt.limit(limit * 3 if limit else 5)).all()

    results: list[ChatAIContextCitation] = []
    for comment, request, author in rows:
        if not _request_visible(request, user):
            continue
        snippet = _trim_text(comment.body or "")
        label = f"Comment by {author.username} on {request.title or f'Request {request.id}'}"
        results.append(
            ChatAIContextCitation(
                id=f"comment:{comment.id}",
                label=label,
                url=f"/requests/{request.id}#comment-{comment.id}",
                snippet=snippet,
                source_type="comment",
            )
        )
        if len(results) >= limit:
            break
    return results


def _request_visible(request: HelpRequest, user: User) -> bool:
    if user.is_admin or request.created_by_user_id == user.id:
        return True
    scope = (request.sync_scope or "").lower()
    user_scope = (user.sync_scope or "").lower()
    if scope == "public":
        return True
    return scope and scope == user_scope


_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def _strip_markup(text: str) -> str:
    if "<" not in text:
        return text
    return _HTML_TAG_PATTERN.sub(" ", text)


def _trim_text(text: str, *, limit: int = 240) -> str:
    sanitized = _strip_markup(text)
    cleaned = " ".join(sanitized.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


__all__ = ["build_ai_chat_context", "ChatAIContextResult", "ChatAIContextCitation"]
