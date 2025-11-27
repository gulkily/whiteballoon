from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app.models import UserProfileHighlight
from app.services import user_profile_highlight_service as service


def _session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _payload_components():
    return {
        "bio_paragraphs": ["Connector"],
        "proof_points": [{"label": "Resource curator", "detail": "Links", "reference": "url"}],
        "quotes": ["quote"],
        "confidence_note": "Based on data",
    }


def test_upsert_auto_creates_record() -> None:
    session = _session()
    with session:
        meta = service.HighlightMeta(
            source_group="harvard",
            llm_model="openai/gpt-5-mini",
            snapshot_last_seen_at=datetime.utcnow(),
            guardrail_issues=[],
        )
        record = service.upsert_auto(
            session,
            user_id=1,
            snapshot_hash="abc",
            meta=meta,
            **_payload_components(),
        )
        session.commit()
    assert record.user_id == 1
    assert record.manual_override is False
    assert record.source_group == "harvard"
    stored = session.get(UserProfileHighlight, 1)
    assert stored is not None


def test_manual_override_blocks_autoupdate() -> None:
    session = _session()
    with session:
        service.set_manual_override(session, user_id=5, text="Custom")
        meta = service.HighlightMeta(
            source_group="harvard",
            llm_model="model",
            snapshot_last_seen_at=datetime.utcnow(),
            guardrail_issues=[],
        )
        record = service.upsert_auto(
            session,
            user_id=5,
            snapshot_hash="hash",
            meta=meta,
            **_payload_components(),
        )
        session.commit()
    assert record.manual_override is True
    assert record.override_text == "Custom"


def test_mark_stale_sets_flag() -> None:
    session = _session()
    with session:
        meta = service.HighlightMeta(
            source_group="test",
            llm_model="model",
            snapshot_last_seen_at=datetime.utcnow(),
            guardrail_issues=[],
        )
        service.upsert_auto(
            session,
            user_id=9,
            snapshot_hash="hash",
            meta=meta,
            **_payload_components(),
        )
        service.mark_stale(session, user_id=9, reason="scan")
        session.commit()
    stored = session.get(UserProfileHighlight, 9)
    assert stored.is_stale is True
    assert stored.stale_reason == "scan"


def test_clear_manual_override_marks_stale() -> None:
    session = _session()
    with session:
        service.set_manual_override(session, user_id=3, text="Manual")
        service.clear_manual_override(session, user_id=3)
        session.commit()
    stored = session.get(UserProfileHighlight, 3)
    assert stored.manual_override is False
    assert stored.is_stale is True
