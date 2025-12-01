from __future__ import annotations

import asyncio
import json
import inspect
from dataclasses import dataclass
from typing import Iterable

from app.config import get_settings
from app.services.comment_llm_insights_service import CommentInsight
from app.services.signal_profile_bio_service import (
    BioPayload,
    ProofPoint,
    build_prompt,
    fallback_bio,
    parse_bio_response,
)
from app.services.signal_profile_snapshot import SignalProfileSnapshot

FORBIDDEN_PHRASES = {
    "rumor",
    "allegedly",
    "unknown",
    "maybe",
    "if true",
    "probably",
}


@dataclass
class BioLLMResult:
    payload: BioPayload
    raw_response: str
    guardrail_issues: list[str]


class SignalProfileBioLLM:
    def __init__(self, *, model: str | None = None, runner: object | None = None):
        self._model = model or "openai/gpt-5-mini"
        if runner is not None:
            self._runner = runner
            self._runner_is_async = asyncio.iscoroutinefunction(getattr(runner, "run", None))
            return

        try:
            from dedalus_labs import AsyncDedalus, DedalusRunner  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional path
            raise RuntimeError(
                "Install 'dedalus-labs' to enable Signal profile glazing."
            ) from exc

        settings = get_settings()
        api_key = settings.dedalus_api_key
        client = AsyncDedalus(api_key=api_key) if api_key else AsyncDedalus()
        self._runner = DedalusRunner(client)
        self._runner_is_async = True

    async def _run_async(self, prompt: str) -> str:
        response = await self._runner.run(input=prompt, model=self._model)
        output = getattr(response, "final_output", "")
        return (output or str(response)).strip()

    def _run(self, prompt: str) -> str:
        if not self._runner_is_async and hasattr(self._runner, "run"):
            response = self._runner.run(input=prompt, model=self._model)
            output = getattr(response, "final_output", "")
            return (output or str(response)).strip()
        return asyncio.run(self._run_async(prompt))

    def generate(
        self,
        snapshot: SignalProfileSnapshot,
        analyses: Iterable[CommentInsight],
    ) -> BioLLMResult:
        prompt = build_prompt(snapshot, analyses)
        fallback = fallback_bio(snapshot, analyses)
        try:
            raw = self._run(prompt)
            payload = parse_bio_response(raw)
        except Exception:
            return BioLLMResult(payload=fallback, raw_response="", guardrail_issues=["llm-error"])

        payload, issues = enforce_guardrails(snapshot, payload, fallback=fallback)
        return BioLLMResult(payload=payload, raw_response=raw, guardrail_issues=issues)


def enforce_guardrails(
    snapshot: SignalProfileSnapshot,
    payload: BioPayload,
    *,
    fallback: BioPayload | None = None,
) -> tuple[BioPayload, list[str]]:
    issues: list[str] = []
    lower_text = " ".join(payload.bio_paragraphs + payload.quotes).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_text:
            issues.append(f"forbidden:{phrase}")
    limit = 80 if snapshot.message_count < 5 else 220
    word_total = sum(len(paragraph.split()) for paragraph in payload.bio_paragraphs)
    if word_total > limit:
        issues.append("length-exceeded")
    if not payload.proof_points:
        issues.append("missing-proof-points")
    if not payload.confidence_note:
        issues.append("missing-confidence")

    if issues and fallback:
        return fallback, issues
    return payload, issues
