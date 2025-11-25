from __future__ import annotations

import pytest

from app.services import request_chat_embeddings


def test_build_and_load_embedding_index(tmp_path, monkeypatch):
    monkeypatch.setattr(request_chat_embeddings, "CACHE_DIR", tmp_path)
    vectors = [
        (101, [1.0, 0.0, 0.0]),
        (102, [0.0, 1.0, 0.0]),
    ]
    index = request_chat_embeddings.build_index(
        request_id=5,
        model="local:test",
        comment_vectors=vectors,
        source_count=4,
    )
    assert index.vector_count == 2
    assert index.aggregate == [0.5, 0.5, 0.0]
    request_chat_embeddings.write_index(index)
    cached = request_chat_embeddings.load_index(5)
    assert cached is not None
    assert cached.vector_count == 2
    assert cached.source_comment_count == 4
    assert cached.comments[0].comment_id == 101
    assert request_chat_embeddings.list_cached_request_ids() == [5]
    similarity = request_chat_embeddings.cosine_similarity(
        cached.aggregate,
        [0.5, 0.5, 0.0],
        norm_a=cached.aggregate_norm,
    )
    assert similarity == pytest.approx(1.0)
    mismatch = request_chat_embeddings.cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])
    assert mismatch == 0.0
