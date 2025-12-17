from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlmodel import Session, select

from app.models import User, UserAttribute
from app.services.peer_auth_service import (
    PEER_AUTH_REVIEWER_ATTRIBUTE_KEY,
    PEER_AUTH_TRUTHY_VALUES,
)


def _is_truthy(value: Optional[str]) -> bool:
    if not value:
        return False
    return value.strip().lower() in PEER_AUTH_TRUTHY_VALUES


@dataclass(slots=True)
class UserPermissionSummary:
    user_id: int
    is_admin: bool
    peer_auth_reviewer: bool
    peer_auth_attribute: Optional[UserAttribute]

    @property
    def peer_auth_updated_at(self):
        if not self.peer_auth_attribute:
            return None
        return self.peer_auth_attribute.updated_at

    @property
    def peer_auth_updated_by(self):
        if not self.peer_auth_attribute:
            return None
        return self.peer_auth_attribute.updated_by_user_id


def load_permission_summaries(
    session: Session,
    users: Iterable[User],
) -> dict[int, UserPermissionSummary]:
    user_ids = [user.id for user in users if user.id is not None]
    if not user_ids:
        return {}

    rows = session.exec(
        select(UserAttribute)
        .where(UserAttribute.user_id.in_(user_ids))
        .where(UserAttribute.key == PEER_AUTH_REVIEWER_ATTRIBUTE_KEY)
    ).all()
    attribute_map: dict[int, UserAttribute] = {}
    for row in rows:
        if row.user_id is None:
            continue
        attribute_map[row.user_id] = row

    summaries: dict[int, UserPermissionSummary] = {}
    for user in users:
        if user.id is None:
            continue
        attribute = attribute_map.get(user.id)
        summaries[user.id] = UserPermissionSummary(
            user_id=user.id,
            is_admin=user.is_admin,
            peer_auth_reviewer=_is_truthy(attribute.value if attribute else None),
            peer_auth_attribute=attribute,
        )
    return summaries
