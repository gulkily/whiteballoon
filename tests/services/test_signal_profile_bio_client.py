from __future__ import annotations

from datetime import datetime

from app.services.comment_llm_insights_service import CommentInsight
from app.services.signal_profile_bio_client import (
    BioLLMResult,
    SignalProfileBioLLM,
    enforce_guardrails,
)
from app.services.signal_profile_bio_service import BioPayload, ProofPoint
from app.services.signal_profile_snapshot import SignalProfileSnapshot


class FakeRunner:
    def __init__(self, output: str):
        self.output = output
        self.calls: list[str] = []

    def run(self, *, input: str, model: str):  # noqa: ANN001
        self.calls.append(model)
        return type("Resp", (), {"final_output": self.output})()


def _snapshot(message_count: int = 10) -> SignalProfileSnapshot:
    now = datetime(2024, 3, 20, 12, 0, 0)
    return SignalProfileSnapshot(
        user_id=5,
        group_slug="test",
        message_count=message_count,
        first_seen_at=now,
        last_seen_at=now,
    )


def _insights() -> list[CommentInsight]:
    return [
        CommentInsight(
            comment_id=1,
            help_request_id=1,
            run_id="r",
            summary="Guiding residents",
            resource_tags=["housing"],
            request_tags=[],
            audience="residents",
            residency_stage="on-site",
            location="",
            location_precision="city",
            urgency="low",
            sentiment="positive",
            tags=[],
            notes="",
            recorded_at="2024-03-20T12:00:00Z",
        )
    ]


def test_enforce_guardrails_flags_forbidden_phrase() -> None:
    payload = BioPayload(
        bio_paragraphs=["Maybe this rumor is big"],
        proof_points=[ProofPoint(label="", detail="", reference="")],
        quotes=[],
        confidence_note="",
    )
    fallback = BioPayload([], [], [], "confidence")
    result, issues = enforce_guardrails(_snapshot(), payload, fallback=fallback)
    assert "forbidden:rumor" in issues
    assert result == fallback


def test_guardrails_length_limit_for_small_message_count() -> None:
    long_para = "word " * 90
    payload = BioPayload(
        bio_paragraphs=[long_para],
        proof_points=[ProofPoint(label="", detail="", reference="")],
        quotes=[],
        confidence_note="note",
    )
    _, issues = enforce_guardrails(_snapshot(message_count=2), payload)
    assert "length-exceeded" in issues


def test_llm_wrapper_returns_fallback_on_bad_json() -> None:
    client = SignalProfileBioLLM(runner=FakeRunner("not-json"))
    result = client.generate(_snapshot(), _insights())
    assert isinstance(result, BioLLMResult)
    assert result.guardrail_issues == ["llm-error"]
