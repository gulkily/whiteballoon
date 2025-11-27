from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.signal_profile_snapshot import (
    LinkStat,
    SignalProfileSnapshot,
    TagStat,
)


@pytest.fixture
def snapshot_sample() -> SignalProfileSnapshot:
    now = datetime(2024, 3, 19, 12, 0, tzinfo=timezone.utc)
    return SignalProfileSnapshot(
        user_id=42,
        group_slug="harvardstcommons",
        message_count=12,
        first_seen_at=now,
        last_seen_at=now,
        top_links=[LinkStat(url="https://partiful.com/e/demo", domain="partiful.com", count=3)],
        top_tags=[TagStat(label="housing", count=5)],
        reaction_counts={"❤️": 4, "😂": 2},
        attachment_counts={"image": 1},
        request_ids=[101, 202],
    )


def test_snapshot_serialization_round_trip(snapshot_sample: SignalProfileSnapshot) -> None:
    payload = snapshot_sample.to_dict()
    restored = SignalProfileSnapshot.from_dict(payload)
    assert restored == snapshot_sample


def test_link_stat_from_dict_handles_defaults() -> None:
    payload = {"url": "https://example.com", "domain": "example.com", "count": "7"}
    stat = LinkStat.from_dict(payload)
    assert stat.count == 7
    assert stat.domain == "example.com"
    assert stat.url == "https://example.com"


def test_tag_stat_from_dict_handles_defaults() -> None:
    payload = {"label": "logistics", "count": "4"}
    stat = TagStat.from_dict(payload)
    assert stat.count == 4
    assert stat.label == "logistics"


def test_from_dict_requires_timestamps(snapshot_sample: SignalProfileSnapshot) -> None:
    data = snapshot_sample.to_dict()
    data["first_seen_at"] = "2024-03-01T00:00:00+00:00"
    restored = SignalProfileSnapshot.from_dict(data)
    assert restored.first_seen_at.isoformat() == "2024-03-01T00:00:00+00:00"
