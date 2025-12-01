from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from textwrap import dedent
from typing import Iterable

from app.services.comment_llm_insights_service import CommentInsight
from app.services.signal_profile_snapshot import LinkStat, SignalProfileSnapshot, TagStat

MAX_ANALYSES_IN_PROMPT = 10
BASE_TONE_RULES = [
    "Celebrate concrete contributions (housing, logistics, funding, events).",
    "Avoid speculation or personal contact details.",
    "Never fabricate facts; cite only provided data.",
    "Highlight links, tags, and reactions as receipts.",
    "Use energetic yet professional language (e.g., 'community catalyst', 'connector').",
    "Bring playful personality—witty, lightly teasing jabs that stay warm and supportive.",
    "Where it fits, add a clever aside or punchline that nods to their receipts.",
]


@dataclass(frozen=True)
class ProofPoint:
    label: str
    detail: str
    reference: str

    def to_dict(self) -> dict[str, str]:
        return {"label": self.label, "detail": self.detail, "reference": self.reference}


@dataclass(frozen=True)
class BioPayload:
    bio_paragraphs: list[str]
    proof_points: list[ProofPoint]
    quotes: list[str]
    confidence_note: str
    source_comment_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "bio_paragraphs": self.bio_paragraphs,
            "proof_points": [point.to_dict() for point in self.proof_points],
            "quotes": self.quotes,
            "confidence_note": self.confidence_note,
            "source_comment_ids": self.source_comment_ids,
        }


def build_prompt(snapshot: SignalProfileSnapshot, analyses: Iterable[CommentInsight]) -> str:
    """Render the prompt text given the snapshot + analyses."""

    analysis_rows = list(analyses)[:MAX_ANALYSES_IN_PROMPT]
    tone_section = "\n".join(f"- {rule}" for rule in BASE_TONE_RULES)
    lines = [
        "You are the Glaze Narrator, crafting celebratory bios for the WhiteBalloon community.",
        "Follow the tone rules strictly and output JSON using the schema described.",
        "",
        "Tone Rules:",
        tone_section,
        "",
        "Snapshot:",
        json.dumps(snapshot.to_dict(), indent=2, default=str),
        "",
        "Analyses (recent first):",
    ]
    if analysis_rows:
        for insight in analysis_rows:
            payload = {
                "comment_id": insight.comment_id,
                "summary": insight.summary,
                "resource_tags": insight.resource_tags,
                "request_tags": insight.request_tags,
                "notes": insight.notes,
                "sentiment": insight.sentiment,
                "recorded_at": insight.recorded_at,
            }
            lines.append(json.dumps(payload, ensure_ascii=False))
    else:
        lines.append("[]")

    lines.append(
        dedent(
            """
            Output JSON with keys: bio_paragraphs (list of strings), proof_points (list of {label, detail, reference}), quotes (list of strings), confidence_note (string).
            Length guidance: keep bio <=80 words when message_count < 5, otherwise up to 220 words.
            Mention at least one concrete link/tag/reaction when available.
            """
        ).strip()
    )
    return "\n".join(lines)


def parse_bio_response(payload: str) -> BioPayload:
    data = json.loads(payload)
    paragraphs = [str(item).strip() for item in data.get("bio_paragraphs", []) if str(item).strip()]
    proof_points = [
        ProofPoint(
            label=str(entry.get("label", "")),
            detail=str(entry.get("detail", "")),
            reference=str(entry.get("reference", "")),
        )
        for entry in data.get("proof_points", [])
        if isinstance(entry, dict)
    ]
    quotes = [str(item).strip() for item in data.get("quotes", []) if str(item).strip()]
    confidence = str(data.get("confidence_note", "").strip()) or ""
    source_comment_ids = [int(value) for value in data.get("source_comment_ids", []) if str(value).isdigit()]
    return BioPayload(
        bio_paragraphs=paragraphs,
        proof_points=proof_points,
        quotes=quotes,
        confidence_note=confidence,
        source_comment_ids=source_comment_ids,
    )


def fallback_bio(snapshot: SignalProfileSnapshot, analyses: Iterable[CommentInsight]) -> BioPayload:
    """Generate a deterministic positive bio when LLM is unavailable."""

    analysis_rows = list(analyses)
    mention = _build_snapshot_highlight(snapshot)
    summary = _compose_summary_text(snapshot, analysis_rows)
    proof_points = _build_proof_points(snapshot)
    quotes = _extract_quotes(analysis_rows)
    confidence = _confidence_line(snapshot)
    return BioPayload(
        bio_paragraphs=[summary, mention],
        proof_points=proof_points,
        quotes=quotes,
        confidence_note=confidence,
        source_comment_ids=[item.comment_id for item in analysis_rows],
    )


# -------- Helpers --------


def _compose_summary_text(snapshot: SignalProfileSnapshot, analyses: list[CommentInsight]) -> str:
    adjectives = ["connector", "builder", "community catalyst"]
    descriptor = adjectives[snapshot.user_id % len(adjectives)]
    first_sentence = (
        f"A {descriptor} with {snapshot.message_count} Signal posts, "
        f"active since {snapshot.first_seen_at.strftime('%b %d, %Y')}"
    )
    if snapshot.top_tags:
        tag_names = ", ".join(tag.label for tag in snapshot.top_tags[:3])
        first_sentence += f", spotlighting {tag_names}"
    sentences = [first_sentence + "."]
    if analyses:
        latest = analyses[-1]
        sentences.append(
            f"Recent notes: {latest.summary or latest.notes or 'sharing updates'}"
        )
    return " ".join(sentences)


def _build_snapshot_highlight(snapshot: SignalProfileSnapshot) -> str:
    if snapshot.message_count < 3:
        prefix = "Early glimpses show"
    else:
        prefix = "Consistently shows"
    parts = []
    if snapshot.top_links:
        domain = snapshot.top_links[0].domain
        parts.append(f"shares resources like {domain}")
    if snapshot.reaction_counts:
        top = max(snapshot.reaction_counts, key=snapshot.reaction_counts.get)
        parts.append(f"sparks {top} reactions")
    if not parts:
        parts.append("stays actively engaged in chat")
    return f"{prefix} someone who {' and '.join(parts)}."


def _build_proof_points(snapshot: SignalProfileSnapshot) -> list[ProofPoint]:
    points: list[ProofPoint] = []
    for link in snapshot.top_links[:2]:
        points.append(
            ProofPoint(
                label="Resource curator",
                detail=f"Shared {link.domain} links",
                reference=link.url,
            )
        )
    for tag in snapshot.top_tags[:2]:
        points.append(
            ProofPoint(
                label="Topic focus",
                detail=f"Contributes to {tag.label} threads",
                reference=tag.label,
            )
        )
    if not points:
        points.append(
            ProofPoint(
                label="Active member",
                detail="Participates in Signal chats",
                reference=",".join(str(rid) for rid in snapshot.request_ids) or "signal",
            )
        )
    return points


def _extract_quotes(analyses: list[CommentInsight]) -> list[str]:
    quotes: list[str] = []
    for analysis in analyses[:3]:
        if analysis.summary:
            quotes.append(analysis.summary[:120])
    if not quotes:
        quotes.append("Building community one chat at a time")
    return quotes


def _confidence_line(snapshot: SignalProfileSnapshot) -> str:
    last_seen = snapshot.last_seen_at.strftime("%Y-%m-%d")
    return f"Based on {snapshot.message_count} Signal messages through {last_seen}."
