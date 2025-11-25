from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

CACHE_DIR = Path("storage/cache/request_chat_embeddings")


@dataclass
class CommentEmbedding:
    comment_id: int
    embedding: list[float]
    norm: float


@dataclass
class RequestEmbeddingIndex:
    request_id: int
    model: str
    generated_at: str
    vector_count: int
    dimensions: int
    comments: list[CommentEmbedding]
    aggregate: list[float]
    aggregate_norm: float
    source_comment_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "generated_at": self.generated_at,
            "vector_count": self.vector_count,
            "dimensions": self.dimensions,
            "aggregate": self.aggregate,
            "aggregate_norm": self.aggregate_norm,
            "source_comment_count": self.source_comment_count,
            "comments": [asdict(comment) for comment in self.comments],
        }


def build_index(
    *,
    request_id: int,
    model: str,
    comment_vectors: Sequence[tuple[int, Sequence[float]]],
    source_count: int,
) -> RequestEmbeddingIndex:
    """Construct an embedding index payload for a request."""
    comments: list[CommentEmbedding] = []
    for comment_id, vector in comment_vectors:
        vector_list = [float(value) for value in vector]
        comments.append(
            CommentEmbedding(
                comment_id=comment_id,
                embedding=vector_list,
                norm=_vector_norm(vector_list),
            )
        )

    aggregate = _average_vectors([comment.embedding for comment in comments])
    dimensions = len(aggregate) if aggregate else 0

    return RequestEmbeddingIndex(
        request_id=request_id,
        model=model,
        generated_at=datetime.utcnow().isoformat(),
        vector_count=len(comments),
        dimensions=dimensions,
        comments=comments,
        aggregate=aggregate,
        aggregate_norm=_vector_norm(aggregate) if aggregate else 0.0,
        source_comment_count=source_count,
    )


def write_index(index: RequestEmbeddingIndex) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = index.to_dict()
    _cache_path(index.request_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def load_index(request_id: int) -> RequestEmbeddingIndex | None:
    path = _cache_path(request_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    comments_payload = data.get("comments", [])
    comments: list[CommentEmbedding] = []
    for entry in comments_payload:
        comments.append(
            CommentEmbedding(
                comment_id=entry["comment_id"],
                embedding=[float(value) for value in entry.get("embedding", [])],
                norm=float(entry.get("norm", 0.0)),
            )
        )
    aggregate = [float(value) for value in data.get("aggregate", [])]
    return RequestEmbeddingIndex(
        request_id=data["request_id"],
        model=data.get("model", ""),
        generated_at=data.get("generated_at", ""),
        vector_count=data.get("vector_count", len(comments)),
        dimensions=data.get("dimensions", len(aggregate)),
        comments=comments,
        aggregate=aggregate,
        aggregate_norm=float(data.get("aggregate_norm", 0.0)),
        source_comment_count=int(data.get("source_comment_count", len(comments))),
    )


def list_cached_request_ids() -> list[int]:
    ids: list[int] = []
    if not CACHE_DIR.exists():
        return ids
    for path in CACHE_DIR.glob("request_*.json"):
        request_id = _parse_request_id(path.name)
        if request_id:
            ids.append(request_id)
    return sorted(ids)


def cosine_similarity(
    vector_a: Sequence[float],
    vector_b: Sequence[float],
    *,
    norm_a: float | None = None,
    norm_b: float | None = None,
) -> float:
    """Compute cosine similarity for two equal-length vectors."""
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    norm_a = norm_a if norm_a is not None else _vector_norm(vector_a)
    norm_b = norm_b if norm_b is not None else _vector_norm(vector_b)
    if not norm_a or not norm_b:
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    return dot / (norm_a * norm_b)


def _average_vectors(vectors: Iterable[Sequence[float]]) -> list[float]:
    vectors = list(vectors)
    if not vectors:
        return []
    dims = len(vectors[0])
    totals = [0.0] * dims
    for vector in vectors:
        if len(vector) != dims:
            continue
        for idx in range(dims):
            totals[idx] += float(vector[idx])
    count = len(vectors)
    if count == 0:
        return []
    return [value / count for value in totals]


def _vector_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector)) if vector else 0.0


def _cache_path(request_id: int) -> Path:
    return CACHE_DIR / f"request_{request_id}.json"


def _parse_request_id(filename: str) -> int | None:
    if not filename.startswith("request_") or not filename.endswith(".json"):
        return None
    raw = filename[len("request_") : -len(".json")]
    if not raw.isdigit():
        return None
    return int(raw)
