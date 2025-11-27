from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models import HelpRequest, RequestComment, User, UserAttribute
from app.services import user_profile_highlight_service
from app.services.comment_llm_insights_service import CommentInsight
from app.services.signal_profile_bio_client import BioLLMResult
from app.services.signal_profile_bio_service import BioPayload, ProofPoint
from app.services.signal_profile_snapshot import SignalProfileSnapshot
from app.tools import signal_profile_snapshot_cli as cli


class DummySession:
    pass


def _make_snapshot(user_id: int, slug: str) -> SignalProfileSnapshot:
    now = datetime(2024, 3, 20, 12, 0, 0)
    return SignalProfileSnapshot(
        user_id=user_id,
        group_slug=slug,
        message_count=1,
        first_seen_at=now,
        last_seen_at=now,
    )


def test_snapshot_users_writes_files(tmp_path: Path) -> None:
    calls: list[int] = []

    def builder(session, user_id, group_slug=None):  # noqa: ANN001
        calls.append(user_id)
        if user_id == 2:
            return None
        return _make_snapshot(user_id, "harvard")

    stats = cli.snapshot_users(
        DummySession(),
        [1, 2],
        output_dir=tmp_path,
        builder=builder,
    )

    assert stats.attempted == 2
    assert stats.generated == 1
    assert stats.skipped == 1
    written = tmp_path / "1-harvard.json"
    assert written.exists()
    payload = written.read_text().strip()
    assert "\"user_id\": 1" in payload
    assert calls == [1, 2]


def _db_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


class FakeLLM:
    def __init__(self, *_, **__):
        self.invocations = 0

    def generate(self, snapshot, analyses):  # noqa: ANN001
        self.invocations += 1
        payload = BioPayload(
            bio_paragraphs=["Glazed paragraph"],
            proof_points=[ProofPoint(label="proof", detail="detail", reference="ref")],
            quotes=[],
            confidence_note="note",
        )
        return BioLLMResult(payload=payload, raw_response="{}", guardrail_issues=[])


def test_freshness_scan_marks_stale(monkeypatch) -> None:
    session = _db_session()
    user = User(username="fresh-user")
    session.add(user)
    session.commit()
    meta = user_profile_highlight_service.HighlightMeta(
        source_group="harvard",
        llm_model="openai/gpt-5-mini",
        snapshot_last_seen_at=datetime(2024, 3, 20, 12, 0, 0),
        guardrail_issues=[],
    )
    user_profile_highlight_service.upsert_auto(
        session,
        user_id=user.id,
        bio_paragraphs=["Existing"],
        proof_points=[],
        quotes=[],
        confidence_note="note",
        snapshot_hash="old",
        meta=meta,
    )
    session.commit()

    new_snapshot = SignalProfileSnapshot(
        user_id=user.id,
        group_slug="harvard",
        message_count=6,
        first_seen_at=datetime(2024, 3, 19),
        last_seen_at=datetime(2024, 3, 22, 12, 0, 0),
    )

    monkeypatch.setattr(
        cli.signal_profile_snapshot_service,
        "build_snapshot",
        lambda session, user_id, group_slug=None: new_snapshot,
    )

    stats = cli.freshness_scan(
        session,
        [user.id],
        dry_run=False,
        group_slug=None,
    )
    session.close()
    assert stats.marked == 1


def test_glaze_users_writes_output(monkeypatch, tmp_path: Path) -> None:
    session = _db_session()
    user = User(username="signal-user")
    session.add(user)
    session.commit()
    session.refresh(user)
    session.add(
        UserAttribute(
            user_id=user.id,
            key="signal_import_group:harvard",
            value="Harvard",
        )
    )
    request = HelpRequest(
        title="[Signal] Harvard",
        description="seed",
        status="open",
        created_by_user_id=user.id,
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    comment = RequestComment(
        help_request_id=request.id,
        user_id=user.id,
        body="Sharing https://example.com",
        created_at=datetime(2024, 3, 20, 12, 0, 0),
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    def fake_insight(comment_id: int) -> CommentInsight:
        return CommentInsight(
            comment_id=comment_id,
            help_request_id=request.id,
            run_id="run",
            summary="Helping",
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

    monkeypatch.setattr(
        cli.signal_profile_snapshot_service,
        "build_snapshot",
        lambda session, user_id, group_slug=None: SignalProfileSnapshot(
            user_id=user_id,
            group_slug="harvard",
            message_count=5,
            first_seen_at=datetime(2024, 3, 19),
            last_seen_at=datetime(2024, 3, 20),
        ),
    )
    monkeypatch.setattr(
        cli.comment_llm_insights_service,
        "get_analysis_by_comment_id",
        fake_insight,
    )
    fake_llm = FakeLLM()
    monkeypatch.setattr(cli, "SignalProfileBioLLM", lambda *_, **__: fake_llm)

    user_id = user.id
    stats, processed = cli.glaze_users(
        session,
        [user_id],
        dry_run=False,
        group_slug=None,
        model=None,
        glaze_dir=tmp_path,
        max_users=None,
        resume_skip=set(),
    )
    session.close()

    assert stats.generated == 1
    assert processed == [user_id]
    output_file = tmp_path / f"{user_id}-harvard.glaze.json"
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["payload"]["bio_paragraphs"] == ["Glazed paragraph"]
    assert fake_llm.invocations == 1
