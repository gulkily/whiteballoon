from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from sqlmodel import Session, select

from app.models import User, UserAttribute
from app.services.user_attribute_service import INVITED_BY_USER_ID_KEY


MAX_INVITE_DEGREE = 3


@dataclass(slots=True)
class InviteGraphNode:
    """Tree node describing a user and the folks they invited."""

    user_id: int
    username: str
    degree: int
    invited_at: Optional[str] = None
    children: list["InviteGraphNode"] = field(default_factory=list)


def build_invite_graph(
    session: Session,
    *,
    root_user_id: int,
    max_degree: int = MAX_INVITE_DEGREE,
) -> Optional[InviteGraphNode]:
    """Return a tree of invite relationships rooted at the given user."""
    if max_degree <= 0:
        max_degree = 0

    root = session.get(User, root_user_id)
    if not root:
        return None

    root_node = InviteGraphNode(
        user_id=root.id,
        username=root.username,
        degree=0,
    )

    if max_degree == 0:
        return root_node

    visited: set[int] = {root.id}
    queue = deque([(root_node, 1)])

    while queue:
        parent_node, degree = queue.popleft()
        if degree > max_degree:
            continue

        invitees = _load_invitees(session, inviter_ids=[parent_node.user_id])
        for invitee_user, invite_attribute in invitees.get(parent_node.user_id, []):
            if invitee_user.id in visited:
                continue
            child_node = InviteGraphNode(
                user_id=invitee_user.id,
                username=invitee_user.username,
                degree=degree,
                invited_at=invite_attribute.created_at.isoformat() if invite_attribute else None,
            )
            parent_node.children.append(child_node)
            visited.add(invitee_user.id)
            queue.append((child_node, degree + 1))

        parent_node.children.sort(key=lambda node: node.username.lower())

    return root_node


def _load_invitees(
    session: Session,
    *,
    inviter_ids: list[int],
) -> dict[int, list[tuple[User, Optional[UserAttribute]]]]:
    if not inviter_ids:
        return {}

    inviter_lookup = {str(inviter_id) for inviter_id in inviter_ids}

    rows = session.exec(
        select(User, UserAttribute)
        .join(UserAttribute, UserAttribute.user_id == User.id)
        .where(UserAttribute.key == INVITED_BY_USER_ID_KEY)
        .where(UserAttribute.value.in_(inviter_lookup))
    ).all()

    by_inviter: dict[int, list[tuple[User, Optional[UserAttribute]]]] = defaultdict(list)
    for user, attribute in rows:
        if not attribute or attribute.value not in inviter_lookup:
            continue
        try:
            inviter_id = int(attribute.value)
        except (TypeError, ValueError):
            continue
        if inviter_id not in by_inviter:
            by_inviter[inviter_id] = []
        by_inviter[inviter_id].append((user, attribute))
    return by_inviter
