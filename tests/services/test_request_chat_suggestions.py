from __future__ import annotations

import math

import pytest

from app.services import request_chat_embeddings, request_chat_search_service, request_chat_suggestions


def make_entry(*, comment_id: int, user_id: int, username: str, body: str, topics: list[str] | None = None) -> request_chat_search_service.ChatSearchEntry:
    tokens = body.lower().split()
    tokens.append(username.lower())
    return request_chat_search_service.ChatSearchEntry(
        comment_id=comment_id,
        user_id=user_id,
        username=username,
        created_at="2024-01-01T00:00:00",
        body=body,
        tokens=tokens,
        topics=topics or [],
        ai_topics=[],
    )


def make_index(
    request_id: int,
    entries: list[request_chat_search_service.ChatSearchEntry],
    participants: dict[str, list[str]],
) -> request_chat_search_service.ChatSearchIndex:
    return request_chat_search_service.ChatSearchIndex(
        request_id=request_id,
        generated_at="2024-01-01T00:00:00",
        entry_count=len(entries),
        participants=participants,
        entries=entries,
    )


def make_embedding(request_id: int, vector: list[float]) -> request_chat_embeddings.RequestEmbeddingIndex:
    norm = math.sqrt(sum(value * value for value in vector))
    return request_chat_embeddings.RequestEmbeddingIndex(
        request_id=request_id,
        model="local:test",
        generated_at="2024-01-01T00:00:00",
        vector_count=1,
        dimensions=len(vector),
        comments=[
            request_chat_embeddings.CommentEmbedding(
                comment_id=request_id * 1000,
                embedding=vector,
                norm=norm,
            )
        ],
        aggregate=vector,
        aggregate_norm=norm,
        source_comment_count=1,
    )


def test_semantic_matches_surface_without_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr(request_chat_suggestions, "CACHE_DIR", tmp_path)
    (tmp_path / "request_2.json").write_text("{}")

    current_entry = make_entry(comment_id=101, user_id=1, username="Alpha", body="Checking new updates")
    other_entry = make_entry(comment_id=201, user_id=2, username="Beta", body="Similar phrasing shows up here")

    chat_indexes = {
        1: make_index(1, [current_entry], {"1": ["alpha"]}),
        2: make_index(2, [other_entry], {"2": ["beta"]}),
    }
    embeddings = {
        1: make_embedding(1, [1.0, 0.0, 0.0]),
        2: make_embedding(2, [1.0, 0.0, 0.0]),
    }

    monkeypatch.setattr(request_chat_search_service, "ensure_chat_index", lambda session, rid: chat_indexes[rid])
    monkeypatch.setattr(request_chat_search_service, "load_chat_index", lambda rid: chat_indexes.get(rid))
    monkeypatch.setattr(request_chat_embeddings, "load_index", lambda rid: embeddings.get(rid))
    monkeypatch.setattr(
        request_chat_suggestions,
        "_serialize_request",
        lambda session, rid: {"id": rid, "title": f"Request {rid}", "status": "open"},
    )

    results = request_chat_suggestions.suggest_related_requests(session=None, help_request_id=1)
    assert len(results) == 1
    result = results[0]
    assert result["request_id"] == 2
    assert result["match_type"] == "semantic"
    assert result["embedding_similarity"] == pytest.approx(1.0)
    assert result["topics"] == []
    assert result["participants"] == []
    assert result["snippet"]["body"] == other_entry.body


def test_hybrid_matches_include_embedding_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(request_chat_suggestions, "CACHE_DIR", tmp_path)
    (tmp_path / "request_2.json").write_text("{}")
    (tmp_path / "request_3.json").write_text("{}")

    current_entry = make_entry(
        comment_id=101,
        user_id=1,
        username="Alex",
        body="Need housing help",
        topics=["housing"],
    )
    other_overlap = make_entry(
        comment_id=201,
        user_id=2,
        username="Alex",
        body="Alex mentioned housing vouchers",
        topics=["housing"],
    )
    other_no_embedding = make_entry(
        comment_id=301,
        user_id=3,
        username="Alex",
        body="Alex can offer rides for housing appointments",
        topics=["housing"],
    )

    chat_indexes = {
        1: make_index(1, [current_entry], {"1": ["alex"]}),
        2: make_index(2, [other_overlap], {"2": ["alex"]}),
        3: make_index(3, [other_no_embedding], {"3": ["alex"]}),
    }
    embeddings = {
        1: make_embedding(1, [0.9, 0.1, 0.0]),
        2: make_embedding(2, [0.92, 0.08, 0.0]),
    }

    monkeypatch.setattr(request_chat_search_service, "ensure_chat_index", lambda session, rid: chat_indexes[rid])
    monkeypatch.setattr(request_chat_search_service, "load_chat_index", lambda rid: chat_indexes.get(rid))
    monkeypatch.setattr(request_chat_embeddings, "load_index", lambda rid: embeddings.get(rid))
    monkeypatch.setattr(
        request_chat_suggestions,
        "_serialize_request",
        lambda session, rid: {"id": rid, "title": f"Request {rid}", "status": "open"},
    )

    results = request_chat_suggestions.suggest_related_requests(session=None, help_request_id=1, limit=5)
    assert [item["request_id"] for item in results] == [2, 3]

    hybrid = results[0]
    assert hybrid["match_type"] == "hybrid"
    assert hybrid["embedding_similarity"] > 0.9
    assert hybrid["topics"] == ["housing"]
    assert hybrid["participants"] == ["alex"]

    overlap_only = results[1]
    assert overlap_only["match_type"] == "overlap"
    assert overlap_only["embedding_similarity"] == 0.0
    assert overlap_only["snippet"]["body"] == other_no_embedding.body
