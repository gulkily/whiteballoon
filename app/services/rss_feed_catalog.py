from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlmodel import Session

from app.models import User
from app.services import user_attribute_service


@dataclass(frozen=True)
class FeedVariant:
    slug: str
    label: str
    description: str
    statuses: tuple[str, ...] | None = None
    pinned_only: bool = False
    include_pending: bool = False
    require_admin: bool = False
    include_invite_circle: bool = False
    viewer_only: bool = False
    limit: int | None = 50

    def build_query_kwargs(self, session: Session, viewer: User) -> dict[str, object]:
        filters: dict[str, object] = {
            "limit": self.limit,
            "pinned_only": self.pinned_only,
            "include_pending": self.include_pending,
        }
        if self.statuses:
            filters["statuses"] = list(self.statuses)
        created_by_ids: Iterable[int] | None = None
        if self.include_invite_circle:
            invitee_ids = user_attribute_service.list_invitee_user_ids(session, inviter_user_id=viewer.id)
            scoped_ids = set(invitee_ids)
            scoped_ids.add(viewer.id)
            created_by_ids = sorted(scoped_ids)
        elif self.viewer_only:
            created_by_ids = [viewer.id]
        if created_by_ids:
            filters["created_by_user_ids"] = created_by_ids
        return filters


RSS_FEED_VARIANTS: dict[str, FeedVariant] = {
    "all-open": FeedVariant(
        slug="all-open",
        label="All open requests",
        description="Live feed of every open request you have permission to view.",
        statuses=("open",),
        limit=60,
    ),
    "circle-open": FeedVariant(
        slug="circle-open",
        label="My invite circle",
        description="Requests created by you or your direct invitees.",
        statuses=("open",),
        include_invite_circle=True,
        limit=60,
    ),
    "completed": FeedVariant(
        slug="completed",
        label="Recently completed",
        description="Latest completions across your network.",
        statuses=("completed",),
        limit=30,
    ),
    "admin-pending": FeedVariant(
        slug="admin-pending",
        label="Admin triage",
        description="Pending requests awaiting review (admins only).",
        statuses=("pending",),
        include_pending=True,
        require_admin=True,
        limit=60,
    ),
}


def get_variant(slug: str) -> FeedVariant | None:
    return RSS_FEED_VARIANTS.get(slug)


def list_variants_for_user(user: User) -> list[FeedVariant]:
    variants: list[FeedVariant] = []
    for variant in RSS_FEED_VARIANTS.values():
        if variant.require_admin and not user.is_admin:
            continue
        variants.append(variant)
    return variants
