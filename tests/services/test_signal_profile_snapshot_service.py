from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

from app.models import HelpRequest, RequestComment, User, UserAttribute
from app.services import signal_profile_snapshot_service
from app.services.signal_profile_snapshot import LinkStat


class DummyInsight:
    def __init__(self, resource_tags: list[str], request_tags: list[str], tags: list[str]):
        self.resource_tags = resource_tags
        self.request_tags = request_tags
        self.tags = tags


def _setup_db() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_build_snapshot_compiles_stats(monkeypatch) -> None:
    session = _setup_db()
    with session:
        user = User(username="signal-user")
        session.add(user)
        session.commit()
        session.refresh(user)

        session.add(
            UserAttribute(
                user_id=user.id,
                key="signal_import_group:harvardstcommons",
                value="Harvard St Commons",
            )
        )
        request = HelpRequest(
            title="[Signal] Harvard St Commons",
            description="seed",
            status="open",
            created_by_user_id=user.id,
        )
        session.add(request)
        session.commit()
        session.refresh(request)

        comment1 = RequestComment(
            help_request_id=request.id,
            user_id=user.id,
            body=(
                "Sharing https://partiful.com/e/vbdJXlwvfid5\n"
                "[attachments: flyer.png]\n"
                "(Reactions: Lucas ❤️)"
            ),
            created_at=datetime(2024, 3, 18, 12, 0, 0),
        )
        comment2 = RequestComment(
            help_request_id=request.id,
            user_id=user.id,
            body="More context https://docs.example.com/plan.pdf",
            created_at=datetime(2024, 3, 19, 12, 0, 0),
        )
        session.add(comment1)
        session.add(comment2)
        session.commit()
        session.refresh(comment1)
        session.refresh(comment2)

        def fake_get_analysis(comment_id: int):
            if comment_id == comment1.id:
                return DummyInsight(["housing"], ["event"], [])
            if comment_id == comment2.id:
                return DummyInsight([], ["logistics"], ["guides"])
            return None

        monkeypatch.setattr(
            signal_profile_snapshot_service.comment_llm_insights_service,
            "get_analysis_by_comment_id",
            fake_get_analysis,
        )

        snapshot = signal_profile_snapshot_service.build_snapshot(session, user.id)

    assert snapshot is not None
    assert snapshot.message_count == 2
    assert snapshot.group_slug == "harvardstcommons"
    assert snapshot.first_seen_at.year == 2024
    assert snapshot.last_seen_at.day == 19
    assert snapshot.reaction_counts.get("❤️") == 1
    assert snapshot.attachment_counts.get("image") == 1

    assert snapshot.top_links[0] == LinkStat(
        url="https://partiful.com/e/vbdJXlwvfid5", domain="partiful.com", count=1
    )
    tag_labels = [tag.label for tag in snapshot.top_tags]
    assert set(tag_labels) == {"housing", "event", "logistics", "guides"}


def test_build_snapshot_missing_group_returns_none(monkeypatch) -> None:
    session = _setup_db()
    with session:
        user = User(username="signal-user")
        session.add(user)
        session.commit()
        session.refresh(user)

        result = signal_profile_snapshot_service.build_snapshot(session, user.id)
    assert result is None
