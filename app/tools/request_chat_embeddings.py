from __future__ import annotations

import argparse
import asyncio
import hashlib
import random
from typing import Iterable, Sequence

from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_engine
from app.models import HelpRequest
from app.services import request_chat_embeddings, request_chat_search_service

DEFAULT_MAX_COMMENTS = 40
DEFAULT_BATCH_SIZE = 16
LOCAL_EMBEDDING_DIMENSIONS = 384


class EmbeddingAdapter:
    label: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:  # pragma: no cover - interface
        raise NotImplementedError


class DedalusEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, model: str | None = None) -> None:
        try:
            from dedalus_labs import AsyncDedalus  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install the 'dedalus-labs' package to fetch embeddings from Dedalus/OpenAI."
            ) from exc

        settings = get_settings()
        api_key = settings.dedalus_api_key
        try:
            if api_key:
                self._client = AsyncDedalus(api_key=api_key)
            else:
                self._client = AsyncDedalus()
        except TypeError:  # pragma: no cover - backwards compatibility when api_key optional
            self._client = AsyncDedalus()
        self._model = model or "text-embedding-3-large"
        self.label = f"dedalus:{self._model}"

    async def _embed_async(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(model=self._model, input=list(texts))
        data = getattr(response, "data", None)
        if not data:
            raise RuntimeError("Dedalus returned an empty embedding response")
        vectors: list[list[float]] = []
        for item in data:
            vector = _coerce_vector(item)
            vectors.append(vector)
        return vectors

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return asyncio.run(self._embed_async(texts))


class LocalEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, dimensions: int = LOCAL_EMBEDDING_DIMENSIONS) -> None:
        self._dimensions = max(32, dimensions)
        self.label = f"local:{self._dimensions}d"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._hash_embedding(text) for text in texts]

    def _hash_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rng = random.Random(digest)
        return [rng.uniform(-1.0, 1.0) for _ in range(self._dimensions)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.request_chat_embeddings",
        description="Generate embedding caches for request chats to power semantic suggestions.",
    )
    parser.add_argument("--request-id", type=int, action="append", dest="request_ids", help="Request ID to index (repeatable)")
    parser.add_argument("--all", action="store_true", help="Process every request in the database")
    parser.add_argument(
        "--max-comments",
        type=int,
        default=DEFAULT_MAX_COMMENTS,
        help="Only embed the newest N comments per request (default: %(default)s)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Texts per embedding batch call (default: %(default)s)",
    )
    parser.add_argument("--model", help="Embedding model alias (Dedalus adapter only)")
    parser.add_argument(
        "--adapter",
        choices=("dedalus", "local"),
        default="dedalus",
        help="Embedding provider (default: dedalus)",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=LOCAL_EMBEDDING_DIMENSIONS,
        help="Local adapter vector dimensions (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute even if an embedding cache already exists",
    )
    return parser


def _resolve_request_ids(session: Session, raw_ids: Iterable[int] | None, include_all: bool) -> list[int]:
    resolved = set(filter(None, raw_ids or []))
    if include_all or not resolved:
        rows = session.exec(select(HelpRequest.id)).all()
        resolved.update(row[0] for row in rows if row[0])
    return sorted(resolved)


def _select_entries(
    index: request_chat_search_service.ChatSearchIndex,
    *,
    max_comments: int,
) -> list[request_chat_search_service.ChatSearchEntry]:
    entries = [entry for entry in index.entries if entry.body]
    if max_comments > 0 and len(entries) > max_comments:
        return entries[-max_comments:]
    return entries


def _chunked(items: Sequence[tuple[int, str]], size: int) -> Iterable[list[tuple[int, str]]]:
    chunk = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _coerce_vector(item: object) -> list[float]:
    if item is None:
        raise RuntimeError("Embedding payload missing vector data")
    vector = None
    if hasattr(item, "embedding"):
        vector = getattr(item, "embedding")
    elif isinstance(item, dict):
        vector = item.get("embedding") or item.get("vector")
    elif isinstance(item, (list, tuple)):
        vector = item
    if vector is None:
        vector = getattr(item, "vector", None)
    if vector is None:
        raise RuntimeError("Unable to read embedding vector from payload")
    return [float(value) for value in vector]


def _build_adapter(ns: argparse.Namespace) -> EmbeddingAdapter:
    if ns.adapter == "local":
        return LocalEmbeddingAdapter(dimensions=ns.dimensions)
    return DedalusEmbeddingAdapter(model=ns.model)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if not ns.request_ids and not ns.all:
        parser.error("Provide --all or at least one --request-id")

    try:
        adapter = _build_adapter(ns)
    except RuntimeError as exc:
        parser.error(str(exc))

    engine = get_engine()
    with Session(engine) as session:
        request_ids = _resolve_request_ids(session, ns.request_ids, ns.all)
        if not request_ids:
            parser.error("No matching requests found")

        for request_id in request_ids:
            existing_index = request_chat_embeddings.load_index(request_id)
            if existing_index and not ns.force:
                print(f"[chat-embed] Request {request_id}: cache exists (use --force to rebuild)")
                continue
            index = request_chat_search_service.ensure_chat_index(session, request_id)
            entries = _select_entries(index, max_comments=max(0, ns.max_comments))
            tasks: list[tuple[int, str]] = []
            for entry in entries:
                body = (entry.body or "").strip()
                if body:
                    tasks.append((entry.comment_id, body))
            if not tasks:
                print(f"[chat-embed] Request {request_id}: no comment text to embed")
                continue
            vectors: list[tuple[int, list[float]]] = []
            batch_size = max(1, ns.batch_size)
            for batch in _chunked(tasks, batch_size):
                batch_ids = [comment_id for comment_id, _ in batch]
                batch_texts = [text for _, text in batch]
                embeddings = adapter.embed(batch_texts)
                if len(embeddings) != len(batch_ids):
                    raise RuntimeError("Embedding provider returned mismatched batch size")
                for comment_id, vector in zip(batch_ids, embeddings):
                    vectors.append((comment_id, vector))
            embedding_index = request_chat_embeddings.build_index(
                request_id=request_id,
                model=adapter.label,
                comment_vectors=vectors,
                source_count=len(entries),
            )
            if not embedding_index.vector_count:
                print(f"[chat-embed] Request {request_id}: embedding generation returned zero vectors")
                continue
            request_chat_embeddings.write_index(embedding_index)
            print(
                "[chat-embed] Request {request} stored {count} vectors via {label} (source comments: {source})".format(
                    request=request_id,
                    count=embedding_index.vector_count,
                    label=adapter.label,
                    source=embedding_index.source_comment_count,
                )
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
