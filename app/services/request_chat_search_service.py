from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
import os
from pathlib import Path
from typing import Callable, Sequence

from sqlmodel import Session

from . import request_comment_service

logger = logging.getLogger(__name__)

CACHE_DIR = Path("storage/cache/request_chats")
TOKEN_PATTERN = re.compile(r"[a-z0-9@#]+")
DEFAULT_RESULT_LIMIT = 20
_CPU_COUNT = os.cpu_count() or 4
DEFAULT_CLASSIFIER_WORKERS = max(2, min(8, _CPU_COUNT))
CLASSIFIER_WORKER_LIMIT = max(
    1,
    int(os.environ.get("REQUEST_CHAT_CLASSIFIER_WORKERS", DEFAULT_CLASSIFIER_WORKERS)),
)

ClassifierFn = Callable[[int, str], list[str]]

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
    ai_topics: list[str]


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
    ai_topics: list[str]
    matched_tokens: list[str]
    anchor: str


def refresh_chat_index(
    session: Session,
    help_request_id: int,
    *,
    extra_classifier: ClassifierFn | None = None,
) -> ChatSearchIndex:
    """Rebuild and persist the chat search index for a request."""
    rows, _ = request_comment_service.list_comments(session, help_request_id)
    entries: list[ChatSearchEntry] = []
    participant_terms: dict[str, list[str]] = {}

    classifier_inputs: list[tuple[ChatSearchEntry, int, str]] = []

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
            ai_topics=[],
        )
        entries.append(entry)
        participant_terms[str(user.id)] = _participant_terms(user.username)
        if extra_classifier:
            classifier_inputs.append((entry, comment.id, normalized_body))

    if extra_classifier and classifier_inputs:
        _apply_parallel_classification(extra_classifier, classifier_inputs)

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
    entries_payload = data.get("entries", [])
    entries: list[ChatSearchEntry] = []
    for entry in entries_payload:
        entries.append(
            ChatSearchEntry(
                comment_id=entry["comment_id"],
                user_id=entry["user_id"],
                username=entry["username"],
                created_at=entry.get("created_at"),
                body=entry["body"],
                tokens=entry.get("tokens", []),
                topics=entry.get("topics", []),
                ai_topics=entry.get("ai_topics", []),
            )
        )
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
        candidate_topics = set(entry.topics) | set(entry.ai_topics)
        if topic_filter and not (topic_filter & candidate_topics):
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
            ai_topics=entry.ai_topics,
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


def _apply_parallel_classification(
    classifier: ClassifierFn,
    workloads: list[tuple[ChatSearchEntry, int, str]],
) -> None:
    """Populate ai_topics concurrently to avoid sequential classifier calls."""
    worker_count = min(len(workloads), CLASSIFIER_WORKER_LIMIT)
    if worker_count <= 1:
        for entry, comment_id, text in workloads:
            entry.ai_topics = classifier(comment_id, text)
        return

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(classifier, comment_id, text): entry for entry, comment_id, text in workloads
        }
        try:
            for future in as_completed(future_map):
                entry = future_map[future]
                entry.ai_topics = future.result()
        except BaseException:
            for future in future_map:
                future.cancel()
            raise


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
