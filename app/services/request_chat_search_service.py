from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from sqlmodel import Session

from . import request_comment_service

logger = logging.getLogger(__name__)

CACHE_DIR = Path("storage/cache/request_chats")
TOKEN_PATTERN = re.compile(r"[a-z0-9@#]+")
DEFAULT_RESULT_LIMIT = 20

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "housing": ("housing", "apartment", "apt", "lease", "room", "shelter"),
    "transport": ("ride", "car", "drive", "transport", "bus", "train"),
    "finance": ("money", "fund", "funds", "cash", "payment", "pay"),
    "medical": ("doctor", "clinic", "medicine", "medical", "prescription"),
    "supplies": ("food", "groceries", "supply", "supplies", "water"),
}


@dataclass
class ChatSearchEntry:
    comment_id: int
    user_id: int
    username: str
    created_at: str | None
    body: str
    tokens: list[str]
    topics: list[str]


@dataclass
class ChatSearchIndex:
    request_id: int
    generated_at: str
    entry_count: int
    participants: dict[str, list[str]]
    entries: list[ChatSearchEntry]


@dataclass
class ChatSearchResult:
    comment_id: int
    user_id: int
    username: str
    created_at: str | None
    body: str
    topics: list[str]
    matched_tokens: list[str]
    anchor: str


def refresh_chat_index(session: Session, help_request_id: int) -> ChatSearchIndex:
    """Rebuild and persist the chat search index for a request."""
    rows, _ = request_comment_service.list_comments(session, help_request_id)
    entries: list[ChatSearchEntry] = []
    participant_terms: dict[str, list[str]] = {}

    for comment, user in rows:
        normalized_body = (comment.body or "").strip()
        lowered = normalized_body.lower()
        tokens = _extract_tokens(lowered)
        topics = _detect_topics(lowered)
        created_at_iso = comment.created_at.isoformat() if comment.created_at else None
        entry = ChatSearchEntry(
            comment_id=comment.id,
            user_id=user.id,
            username=user.username,
            created_at=created_at_iso,
            body=normalized_body,
            tokens=tokens,
            topics=topics,
        )
        entries.append(entry)
        participant_terms[str(user.id)] = _participant_terms(user.username)

    index = ChatSearchIndex(
        request_id=help_request_id,
        generated_at=datetime.utcnow().isoformat(),
        entry_count=len(entries),
        participants=participant_terms,
        entries=entries,
    )
    _write_cache(index)
    logger.info("[%s] Request chat index refreshed (%s entries)", help_request_id, len(entries))
    return index


def load_chat_index(help_request_id: int) -> ChatSearchIndex | None:
    cache_path = _cache_path(help_request_id)
    if not cache_path.exists():
        return None
    data = json.loads(cache_path.read_text())
    entries = [ChatSearchEntry(**entry) for entry in data.get("entries", [])]
    return ChatSearchIndex(
        request_id=data["request_id"],
        generated_at=data["generated_at"],
        entry_count=data["entry_count"],
        participants=data.get("participants", {}),
        entries=entries,
    )


def ensure_chat_index(session: Session, help_request_id: int) -> ChatSearchIndex:
    index = load_chat_index(help_request_id)
    if index:
        return index
    return refresh_chat_index(session, help_request_id)


def search_chat(
    session: Session,
    help_request_id: int,
    *,
    query: str = "",
    participant_ids: Sequence[int] | None = None,
    topics: Sequence[str] | None = None,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> tuple[ChatSearchIndex, list[ChatSearchResult]]:
    index = ensure_chat_index(session, help_request_id)
    query_tokens = _extract_tokens(query.lower()) if query else []
    participant_filter = set(participant_ids or [])
    topic_filter = {topic.lower() for topic in topics or [] if topic}
    matches: list[ChatSearchResult] = []

    for entry in index.entries:
        if participant_filter and entry.user_id not in participant_filter:
            continue
        if topic_filter and not (topic_filter & set(entry.topics)):
            continue
        matched_tokens = _match_tokens(entry.tokens, query_tokens)
        if query_tokens and not matched_tokens:
            continue
        result = ChatSearchResult(
            comment_id=entry.comment_id,
            user_id=entry.user_id,
            username=entry.username,
            created_at=entry.created_at,
            body=entry.body,
            topics=entry.topics,
            matched_tokens=matched_tokens,
            anchor=f"comment-{entry.comment_id}",
        )
        matches.append(result)
        if len(matches) >= limit:
            break

    return index, matches


def serialize_result(result: ChatSearchResult) -> dict[str, object]:
    return asdict(result)


def _extract_tokens(text: str) -> list[str]:
    tokens = set(TOKEN_PATTERN.findall(text))
    return sorted(tokens)


def _participant_terms(username: str) -> list[str]:
    terms = set()
    lowered = username.lower()
    terms.add(lowered)
    terms.update(part.strip() for part in lowered.split() if part.strip())
    return sorted(terms)


def _detect_topics(text: str) -> list[str]:
    found: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(topic)
    return found


def _match_tokens(entry_tokens: list[str], query_tokens: list[str]) -> list[str]:
    if not query_tokens:
        return []
    entry_set = set(entry_tokens)
    return sorted(token for token in query_tokens if token in entry_set)


def _write_cache(index: ChatSearchIndex) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "request_id": index.request_id,
        "generated_at": index.generated_at,
        "entry_count": index.entry_count,
        "participants": index.participants,
        "entries": [asdict(entry) for entry in index.entries],
    }
    _cache_path(index.request_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def _cache_path(help_request_id: int) -> Path:
    return CACHE_DIR / f"request_{help_request_id}.json"
