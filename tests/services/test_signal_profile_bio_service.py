from __future__ import annotations

from datetime import datetime

from app.services.comment_llm_insights_service import CommentInsight
from app.services.signal_profile_bio_service import (
    BioPayload,
    ProofPoint,
    build_prompt,
    fallback_bio,
    parse_bio_response,
)
from app.services.signal_profile_snapshot import LinkStat, SignalProfileSnapshot, TagStat


def _sample_snapshot() -> SignalProfileSnapshot:
    now = datetime(2024, 3, 20, 12, 0, 0)
    return SignalProfileSnapshot(
        user_id=42,
        group_slug="harvardstcommons",
        message_count=12,
        first_seen_at=now,
        last_seen_at=now,
        top_links=[LinkStat(url="https://partiful.com/e/vbdJX", domain="partiful.com", count=2)],
        top_tags=[TagStat(label="housing", count=4)],
        reaction_counts={"❤️": 5},
        attachment_counts={"image": 1},
        request_ids=[123],
    )


def _insight(comment_id: int, summary: str) -> CommentInsight:
    return CommentInsight(
        comment_id=comment_id,
        help_request_id=999,
        run_id="run",
        summary=summary,
        resource_tags=["housing"],
        request_tags=["event"],
        audience="residents",
        residency_stage="on-site",
        location="",
        location_precision="city",
        urgency="low",
        sentiment="positive",
        tags=["guides"],
        notes="",
        recorded_at="2024-03-20T12:00:00Z",
    )


def test_build_prompt_includes_snapshot_and_rules() -> None:
    prompt = build_prompt(_sample_snapshot(), [_insight(1, "Helping with Cory visit")])
    assert "partiful.com" in prompt
    assert "Tone Rules" in prompt
    assert "Helping with Cory visit" in prompt
    assert "bio_paragraphs" in prompt


def test_parse_bio_response_creates_payload() -> None:
    payload = parse_bio_response(
        """
        {
          "bio_paragraphs": ["Test paragraph"],
          "proof_points": [{"label": "Resource curator", "detail": "Shared link", "reference": "http://example.com"}],
          "quotes": ["quote"],
          "confidence_note": "Based on data",
          "source_comment_ids": [1, 2]
        }
        """
    )
    assert isinstance(payload, BioPayload)
    assert payload.bio_paragraphs == ["Test paragraph"]
    assert payload.proof_points == [
        ProofPoint(label="Resource curator", detail="Shared link", reference="http://example.com")
    ]
    assert payload.quotes == ["quote"]
    assert payload.source_comment_ids == [1, 2]


def test_fallback_bio_mentions_links_and_confidence() -> None:
    snapshot = _sample_snapshot()
    result = fallback_bio(snapshot, [_insight(1, "Hosting founders"), _insight(2, "Sharing rooms")])
    assert "connector" in result.bio_paragraphs[0]
    assert any("partiful.com" in point.reference for point in result.proof_points)
    assert "Based on 12 Signal messages" in result.confidence_note
