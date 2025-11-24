from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from sqlmodel import Session

from . import request_comment_service

logger = logging.getLogger(__name__)

CACHE_DIR = Path("storage/cache/request_chats")
TOKEN_PATTERN = re.compile(r"[a-z0-9@#]+")

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
