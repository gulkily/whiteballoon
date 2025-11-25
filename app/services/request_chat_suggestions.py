from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, select

from app.models import HelpRequest
from . import request_chat_search_service

CACHE_DIR = request_chat_search_service.CACHE_DIR


def suggest_related_requests(
    session: Session,
    help_request_id: int,
    *,
    limit: int = 3,
    min_overlap: int = 2,
) -> list[dict[str, object]]:
    """Return related chat snippets from other requests based on topic/entity overlap."""
    current_index = request_chat_search_service.ensure_chat_index(session, help_request_id)
    current_topics = _aggregate_topics(current_index)
    current_participants = _aggregate_participants(current_index)

    if not current_topics and not current_participants:
        return []

    scores: list[tuple[int, float, dict[str, object]]] = []
    for cache_file in CACHE_DIR.glob("request_*.json"):
        other_id = _parse_request_id(cache_file.name)
        if not other_id or other_id == help_request_id:
            continue
        other_index = request_chat_search_service.load_chat_index(other_id)
        if not other_index or not other_index.entries:
            continue
        overlap_topics = current_topics & _aggregate_topics(other_index)
        overlap_people = current_participants & _aggregate_participants(other_index)
        score = len(overlap_topics) * 1.5 + len(overlap_people)
        if score < min_overlap:
            continue
        snippet = _top_snippet(other_index, overlap_topics, overlap_people)
        scores.append(
            (
                other_id,
                score,
                {
                    "request_id": other_id,
                    "score": score,
                    "topics": sorted(overlap_topics),
                    "participants": sorted(overlap_people),
                    "snippet": snippet,
                },
            )
        )

    scores.sort(key=lambda item: item[1], reverse=True)
    related: list[dict[str, object]] = []
    for other_id, _score, payload in scores[:limit]:
        payload["request"] = _serialize_request(session, other_id)
        related.append(payload)
    return related


def _aggregate_topics(index: request_chat_search_service.ChatSearchIndex) -> set[str]:
    topics: set[str] = set()
    for entry in index.entries:
        topics.update(entry.topics)
        topics.update(entry.ai_topics)
    return topics


def _aggregate_participants(index: request_chat_search_service.ChatSearchIndex) -> set[str]:
    names: set[str] = set()
    for terms in index.participants.values():
        names.update(terms)
    return names


def _parse_request_id(filename: str) -> int | None:
    if not filename.startswith("request_") or not filename.endswith(".json"):
        return None
    number = filename[len("request_") : -len(".json")]
    if not number.isdigit():
        return None
    return int(number)


def _top_snippet(
    index: request_chat_search_service.ChatSearchIndex,
    overlap_topics: set[str],
    overlap_people: set[str],
) -> dict[str, object] | None:
    for entry in index.entries:
        if overlap_topics.intersection(entry.topics) or overlap_people.intersection(entry.tokens):
            return {
                "body": entry.body,
                "anchor": f"comment-{entry.comment_id}",
                "topics": entry.topics,
                "ai_topics": entry.ai_topics,
                "username": entry.username,
                "created_at": entry.created_at,
            }
    return None


def _serialize_request(session: Session, request_id: int) -> dict[str, object] | None:
    request = session.get(HelpRequest, request_id)
    if not request:
        return None
    return {
        "id": request.id,
        "title": request.title,
        "status": request.status,
    }
