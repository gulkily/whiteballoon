from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class LinkStat:
    """Counts how often a user shared a specific URL."""

    url: str
    domain: str
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {"url": self.url, "domain": self.domain, "count": self.count}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LinkStat":
        return cls(
            url=str(payload.get("url", "")),
            domain=str(payload.get("domain", "")),
            count=int(payload.get("count", 0)),
        )


@dataclass(frozen=True)
class TagStat:
    """Summarizes the tags associated with a user's Signal comments."""

    label: str
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "count": self.count}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TagStat":
        return cls(label=str(payload.get("label", "")), count=int(payload.get("count", 0)))


@dataclass(frozen=True)
class SignalProfileSnapshot:
    """Normalized snapshot of Signal-imported activity for one user."""

    user_id: int
    group_slug: str
    message_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    top_links: list[LinkStat] = field(default_factory=list)
    top_tags: list[TagStat] = field(default_factory=list)
    reaction_counts: dict[str, int] = field(default_factory=dict)
    attachment_counts: dict[str, int] = field(default_factory=dict)
    request_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "group_slug": self.group_slug,
            "message_count": self.message_count,
            "first_seen_at": self.first_seen_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "top_links": [link.to_dict() for link in self.top_links],
            "top_tags": [tag.to_dict() for tag in self.top_tags],
            "reaction_counts": dict(self.reaction_counts),
            "attachment_counts": dict(self.attachment_counts),
            "request_ids": list(self.request_ids),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SignalProfileSnapshot":
        return cls(
            user_id=int(payload["user_id"]),
            group_slug=str(payload["group_slug"]),
            message_count=int(payload.get("message_count", 0)),
            first_seen_at=_parse_datetime(payload.get("first_seen_at")),
            last_seen_at=_parse_datetime(payload.get("last_seen_at")),
            top_links=[LinkStat.from_dict(entry) for entry in payload.get("top_links", [])],
            top_tags=[TagStat.from_dict(entry) for entry in payload.get("top_tags", [])],
            reaction_counts={str(k): int(v) for k, v in payload.get("reaction_counts", {}).items()},
            attachment_counts={
                str(k): int(v) for k, v in payload.get("attachment_counts", {}).items()
            },
            request_ids=[int(value) for value in payload.get("request_ids", [])],
        )

    @classmethod
    def empty(cls, user_id: int, group_slug: str) -> "SignalProfileSnapshot":
        now = datetime.utcnow()
        return cls(
            user_id=user_id,
            group_slug=group_slug,
            message_count=0,
            first_seen_at=now,
            last_seen_at=now,
        )

    def merge_links(self, links: Iterable[LinkStat]) -> "SignalProfileSnapshot":
        combined = list(self.top_links)
        combined.extend(links)
        return SignalProfileSnapshot(
            user_id=self.user_id,
            group_slug=self.group_slug,
            message_count=self.message_count,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            top_links=combined,
            top_tags=self.top_tags,
            reaction_counts=self.reaction_counts,
            attachment_counts=self.attachment_counts,
            request_ids=self.request_ids,
        )


def _parse_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw)
    if isinstance(raw, str) and raw:
        return datetime.fromisoformat(raw)
    raise ValueError("Expected datetime-compatible value")
