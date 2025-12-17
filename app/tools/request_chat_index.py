from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections import defaultdict
from typing import Callable, Iterable

from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_engine
from app.models import HelpRequest, RequestComment
from app.dedalus import logging as dedalus_logging
from app.services import request_chat_search_service

logger = logging.getLogger(__name__)


class LLMTopicClassifier:
    """Optional Dedalus-powered classifier for richer topic tags."""

    def __init__(self, model: str | None = None) -> None:
        try:
            from dedalus_labs import AsyncDedalus, DedalusRunner  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install the 'dedalus-labs' package to enable --llm classification."
            ) from exc

        settings = get_settings()
        api_key = settings.dedalus_api_key
        try:
            if api_key:
                client = AsyncDedalus(api_key=api_key)
            else:
                client = AsyncDedalus()
        except TypeError:  # pragma: no cover - backwards compatibility when api_key optional
            client = AsyncDedalus()

        self._runner = DedalusRunner(client)
        self._model = model or "openai/gpt-5-mini"

    async def _classify_async(self, *, comment_id: int, text: str) -> list[str]:
        instructions = (
            "You label mutual-aid chat comments with short topic tags. "
            "Return ONLY a JSON array of lowercase tags (kebab-case). "
            "Aim for 1-4 tags describing needs, offers, or logistics."
        )
        prompt = (
            f"{instructions}\n\n"
            f"Comment ID: {comment_id}\n"
            f"Text:\n{text.strip()}\n"
            "Respond with JSON only."
        )
        response = await self._runner.run(input=prompt, model=self._model)
        output = getattr(response, "final_output", "") or str(response)
        return self._parse_tags(output)

    def classify(
        self,
        *,
        comment_id: int,
        text: str,
        request_id: int | None = None,
    ) -> list[str]:
        prompt = text
        run_id = dedalus_logging.start_logged_run(
            user_id="cli",
            entity_type="request_chat",
            entity_id=str(request_id) if request_id else None,
            model=self._model,
            prompt=prompt,
            context_hash=str(comment_id),
        )
        try:
            result = asyncio.run(self._classify_async(comment_id=comment_id, text=text))
        except Exception as exc:  # pragma: no cover - logging path
            dedalus_logging.finalize_logged_run(
                run_id=run_id,
                response=None,
                status="error",
                error=str(exc),
            )
            raise
        dedalus_logging.finalize_logged_run(
            run_id=run_id,
            response=json.dumps(result),
            status="success",
        )
        return result

    @staticmethod
    def _parse_tags(raw_output: str) -> list[str]:
        cleaned = raw_output.strip()
        if not cleaned:
            return []
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            parts = [chunk.strip().lower() for chunk in cleaned.replace("\n", ",").split(",")]
            return [part for part in parts if part]
        if isinstance(payload, list):
            tags: list[str] = []
            for item in payload:
                if isinstance(item, str) and item:
                    tags.append(item.strip().lower())
            return tags
        return []


ClassifierFactory = Callable[[int, str], list[str]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.request_chat_index",
        description="Rebuild request chat search caches and optionally enrich topics via an LLM.",
    )
    parser.add_argument(
        "--request-id",
        type=int,
        action="append",
        dest="request_ids",
        help="Specific request ID to process (repeatable)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every request in the database",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM topic suggestions for selected comments",
    )
    parser.add_argument(
        "--llm-comment",
        type=int,
        action="append",
        dest="llm_comments",
        help="Comment ID to send through the LLM classifier (repeatable)",
    )
    parser.add_argument(
        "--llm-latest",
        type=int,
        default=0,
        help="Per request, send the newest N comments to the LLM",
    )
    parser.add_argument(
        "--llm-all",
        action="store_true",
        help="Send every processed comment to the LLM (use cautiously)",
    )
    parser.add_argument(
        "--model",
        help="Override the default LLM model alias",
    )
    return parser


def _resolve_request_ids(session: Session, ids: Iterable[int] | None, include_all: bool) -> list[int]:
    resolved = {value for value in (ids or []) if value}
    if include_all or not resolved:
        rows = session.exec(select(HelpRequest.id)).all()
        resolved.update(row for row in rows if row)
    return sorted(resolved)


def _map_explicit_comment_ids(session: Session, comment_ids: Iterable[int] | None) -> dict[int, set[int]]:
    mapping: dict[int, set[int]] = defaultdict(set)
    ids = [cid for cid in (comment_ids or []) if cid]
    if not ids:
        return mapping
    stmt = select(RequestComment.id, RequestComment.help_request_id).where(RequestComment.id.in_(ids))
    for comment_id, request_id in session.exec(stmt):
        mapping[request_id].add(comment_id)
    return mapping


def _latest_comment_ids(session: Session, request_id: int, limit: int) -> set[int]:
    if limit <= 0:
        return set()
    stmt = (
        select(RequestComment.id)
        .where(RequestComment.help_request_id == request_id)
        .order_by(RequestComment.created_at.desc())
        .limit(limit)
    )
    return {comment_id for (comment_id,) in session.exec(stmt)}


def _build_classifier(
    adapter: LLMTopicClassifier | None,
    *,
    allow_all: bool,
    allowed_comment_ids: set[int],
    request_id: int,
) -> request_chat_search_service.ClassifierFn | None:
    if not adapter:
        return None

    allow_all_scope = allow_all or not allowed_comment_ids
    allowed = set(allowed_comment_ids)

    request_scope = request_id

    def classify(comment_id: int, text: str) -> list[str]:
        if not allow_all_scope and comment_id not in allowed:
            return []
        return adapter.classify(comment_id=comment_id, text=text, request_id=request_scope)

    return classify


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if not ns.request_ids and not ns.all:
        parser.error("Provide --all or at least one --request-id")

    if ns.llm and not (ns.llm_all or ns.llm_comments or ns.llm_latest):
        parser.error("Specify --llm-all, --llm-comment, or --llm-latest when enabling --llm")

    adapter: LLMTopicClassifier | None = None
    if ns.llm:
        try:
            adapter = LLMTopicClassifier(model=ns.model)
        except RuntimeError as exc:
            parser.error(str(exc))

    engine = get_engine()
    try:
        with Session(engine) as session:
            request_ids = _resolve_request_ids(session, ns.request_ids, ns.all)
            if not request_ids:
                parser.error("No matching requests found")

            explicit_map = _map_explicit_comment_ids(session, ns.llm_comments)

            for request_id in request_ids:
                allowed_ids = set(explicit_map.get(request_id, set()))
                allowed_ids.update(_latest_comment_ids(session, request_id, ns.llm_latest))
                classifier = _build_classifier(
                    adapter,
                    allow_all=bool(ns.llm_all),
                    allowed_comment_ids=allowed_ids,
                    request_id=request_id,
                )
                index = request_chat_search_service.refresh_chat_index(
                    session,
                    request_id,
                    extra_classifier=classifier,
                )
                scope = "llm+rule" if classifier else "rule-only"
                print(
                    f"[chat-index] Request {request_id}: {index.entry_count} comments indexed ({scope} topics)"
                )
    except KeyboardInterrupt:
        logger.warning("Chat index rebuild interrupted by operator.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
