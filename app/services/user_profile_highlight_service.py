from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlmodel import Session, select

from app.models import UserProfileHighlight

DEFAULT_STALE_DAYS = 14


@dataclass(frozen=True)
class HighlightRecord:
    user_id: int
    bio_paragraphs: list[str]
    proof_points: list[dict[str, str]]
    quotes: list[str]
    confidence_note: str
    source_group: Optional[str]
    snapshot_hash: str
    snapshot_last_seen_at: datetime
    llm_model: Optional[str]
    guardrail_issues: list[str]
    generated_at: datetime
    stale_after: Optional[datetime]
    is_stale: bool
    stale_reason: Optional[str]
    manual_override: bool
    override_text: Optional[str]


@dataclass(frozen=True)
class HighlightMeta:
    source_group: Optional[str]
    llm_model: Optional[str]
    snapshot_last_seen_at: datetime
    guardrail_issues: list[str]
    stale_after: Optional[datetime] = None


def get(session: Session, user_id: int) -> HighlightRecord | None:
    row = session.get(UserProfileHighlight, user_id)
    if not row:
        return None
    return _to_record(row)


def list_highlights(session: Session, user_ids: Iterable[int] | None = None) -> list[HighlightRecord]:
    stmt = select(UserProfileHighlight)
    if user_ids is not None:
        ids = [int(uid) for uid in user_ids]
        if not ids:
            return []
        stmt = stmt.where(UserProfileHighlight.user_id.in_(ids))
    rows = session.exec(stmt).all()
    return [_to_record(row) for row in rows]


def upsert_auto(
    session: Session,
    *,
    user_id: int,
    bio_paragraphs: list[str],
    proof_points: list[dict[str, str]],
    quotes: list[str],
    confidence_note: str,
    snapshot_hash: str,
    meta: HighlightMeta,
) -> HighlightRecord:
    highlight = session.get(UserProfileHighlight, user_id)
    if highlight and highlight.manual_override:
        return _to_record(highlight)

    now = datetime.utcnow()
    stale_after = meta.stale_after or now + timedelta(days=DEFAULT_STALE_DAYS)
    payload_text = "\n\n".join([paragraph.strip() for paragraph in bio_paragraphs if paragraph.strip()])
    proof_points_json = json.dumps(proof_points, ensure_ascii=False)
    quotes_json = json.dumps(quotes, ensure_ascii=False)
    guardrail_json = json.dumps(meta.guardrail_issues, ensure_ascii=False)

    if not highlight:
        highlight = UserProfileHighlight(
            user_id=user_id,
            bio_text=payload_text,
            proof_points_json=proof_points_json,
            quotes_json=quotes_json,
            confidence_note=confidence_note,
            source_group=meta.source_group,
            snapshot_hash=snapshot_hash,
            snapshot_last_seen_at=meta.snapshot_last_seen_at,
            llm_model=meta.llm_model,
            guardrail_issues_json=guardrail_json,
            generated_at=now,
            stale_after=stale_after,
            is_stale=False,
            manual_override=False,
            override_text=None,
            created_at=now,
            updated_at=now,
        )
        session.add(highlight)
    else:
        highlight.bio_text = payload_text
        highlight.proof_points_json = proof_points_json
        highlight.quotes_json = quotes_json
        highlight.source_group = meta.source_group
        highlight.snapshot_hash = snapshot_hash
        highlight.snapshot_last_seen_at = meta.snapshot_last_seen_at
        highlight.llm_model = meta.llm_model
        highlight.guardrail_issues_json = guardrail_json
        highlight.generated_at = now
        highlight.stale_after = stale_after
        highlight.is_stale = False
        highlight.stale_reason = None
        highlight.manual_override = False
        highlight.override_text = None
        highlight.confidence_note = confidence_note
        highlight.updated_at = now

    session.flush()
    return _to_record(highlight)


def set_manual_override(
    session: Session,
    *,
    user_id: int,
    text: str,
) -> HighlightRecord:
    now = datetime.utcnow()
    highlight = session.get(UserProfileHighlight, user_id)
    if not highlight:
        highlight = UserProfileHighlight(
            user_id=user_id,
            bio_text=text,
            proof_points_json=json.dumps([], ensure_ascii=False),
            quotes_json=json.dumps([], ensure_ascii=False),
            confidence_note=None,
            source_group=None,
            snapshot_hash="manual",
            snapshot_last_seen_at=now,
            llm_model=None,
            guardrail_issues_json=json.dumps([], ensure_ascii=False),
            generated_at=now,
            stale_after=None,
            is_stale=False,
            manual_override=True,
            override_text=text,
            created_at=now,
            updated_at=now,
        )
        session.add(highlight)
    else:
        highlight.manual_override = True
        highlight.override_text = text
        highlight.bio_text = text
        highlight.confidence_note = None
        highlight.updated_at = now
        highlight.is_stale = False
        highlight.stale_reason = None
    session.flush()
    return _to_record(highlight)


def clear_manual_override(session: Session, *, user_id: int) -> HighlightRecord | None:
    highlight = session.get(UserProfileHighlight, user_id)
    if not highlight:
        return None
    highlight.manual_override = False
    highlight.override_text = None
    highlight.is_stale = True
    highlight.stale_reason = "manual-override-cleared"
    highlight.updated_at = datetime.utcnow()
    session.flush()
    return _to_record(highlight)


def mark_stale(session: Session, *, user_id: int, reason: str) -> HighlightRecord | None:
    highlight = session.get(UserProfileHighlight, user_id)
    if not highlight:
        return None
    highlight.is_stale = True
    highlight.stale_reason = reason
    highlight.updated_at = datetime.utcnow()
    session.flush()
    return _to_record(highlight)


def _to_record(row: UserProfileHighlight) -> HighlightRecord:
    paragraphs = [part.strip() for part in (row.bio_text or "").split("\n\n") if part.strip()]
    proof_points = []
    quotes = []
    guardrail = []
    try:
        proof_points = json.loads(row.proof_points_json or "[]")
    except json.JSONDecodeError:
        proof_points = []
    try:
        quotes = json.loads(row.quotes_json or "[]")
    except json.JSONDecodeError:
        quotes = []
    try:
        guardrail = json.loads(row.guardrail_issues_json or "[]")
    except json.JSONDecodeError:
        guardrail = []
    return HighlightRecord(
        user_id=row.user_id,
        bio_paragraphs=paragraphs,
        proof_points=[item for item in proof_points if isinstance(item, dict)],
        quotes=[str(item) for item in quotes],
        confidence_note=row.confidence_note or "",
        source_group=row.source_group,
        snapshot_hash=row.snapshot_hash,
        snapshot_last_seen_at=row.snapshot_last_seen_at,
        llm_model=row.llm_model,
        guardrail_issues=[str(item) for item in guardrail],
        generated_at=row.generated_at,
        stale_after=row.stale_after,
        is_stale=row.is_stale,
        stale_reason=row.stale_reason,
        manual_override=row.manual_override,
        override_text=row.override_text,
    )
