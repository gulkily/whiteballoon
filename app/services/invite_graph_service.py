from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlmodel import Session, select

from app.models import User, UserAttribute
from app.services.user_attribute_service import INVITED_BY_USER_ID_KEY


MAX_INVITE_DEGREE = 3
DEFAULT_MAP_DEGREE = 2


@dataclass(slots=True)
class InviteGraphNode:
    """Tree node describing a user and the folks they invited."""

    user_id: int
    username: str
    degree: int
    invited_at: Optional[str] = None
    children: list["InviteGraphNode"] = field(default_factory=list)


@dataclass(slots=True)
class InviteAncestor:
    user_id: int
    username: str
    degree: int
    invited_at: Optional[str] = None


@dataclass(slots=True)
class InviteMapPayload:
    root: InviteGraphNode
    upstream: list[InviteAncestor]


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


def build_bidirectional_invite_map(
    session: Session,
    *,
    root_user_id: int,
    max_degree: int = DEFAULT_MAP_DEGREE,
) -> Optional[InviteMapPayload]:
    """Return upstream and downstream invite relationships limited to `max_degree`."""

    downstream = build_invite_graph(session, root_user_id=root_user_id, max_degree=max_degree)
    if not downstream:
        return None

    upstream = _load_upstream_chain(session, start_user_id=root_user_id, max_degree=max_degree)
    return InviteMapPayload(root=downstream, upstream=upstream)


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


def _load_upstream_chain(
    session: Session,
    *,
    start_user_id: int,
    max_degree: int,
) -> list[InviteAncestor]:
    if max_degree <= 0:
        return []

    ancestors: list[InviteAncestor] = []
    degree = 1
    current_user_id = start_user_id
    visited: set[int] = {start_user_id}

    while degree <= max_degree:
        attribute = _load_inviter_attribute(session, user_id=current_user_id)
        if not attribute or not attribute.value:
            break
        try:
            inviter_id = int(attribute.value)
        except (TypeError, ValueError):
            break

        if inviter_id in visited:
            break

        inviter = session.get(User, inviter_id)
        if not inviter:
            break

        ancestors.append(
            InviteAncestor(
                user_id=inviter.id,
                username=inviter.username,
                degree=degree,
                invited_at=attribute.created_at.isoformat() if attribute.created_at else None,
            )
        )

        visited.add(inviter_id)
        current_user_id = inviter_id
        degree += 1

    return ancestors


def _load_inviter_attribute(session: Session, *, user_id: int) -> Optional[UserAttribute]:
    return session.exec(
        select(UserAttribute)
        .where(UserAttribute.user_id == user_id)
        .where(UserAttribute.key == INVITED_BY_USER_ID_KEY)
    ).first()


def serialize_invite_map(payload: InviteMapPayload) -> dict[str, Any]:
    return {
        "root": _serialize_graph_node(payload.root),
        "upstream": [_serialize_ancestor(ancestor) for ancestor in payload.upstream],
    }


def deserialize_invite_map(data: dict[str, Any]) -> InviteMapPayload:
    root_data = data.get("root")
    if not root_data:
        raise ValueError("Invite map payload missing root node")
    upstream_data = data.get("upstream", [])
    return InviteMapPayload(
        root=_deserialize_graph_node(root_data),
        upstream=[_deserialize_ancestor(item) for item in upstream_data],
    )


def _serialize_graph_node(node: InviteGraphNode) -> dict[str, Any]:
    return {
        "user_id": node.user_id,
        "username": node.username,
        "degree": node.degree,
        "invited_at": node.invited_at,
        "children": [_serialize_graph_node(child) for child in node.children],
    }


def _deserialize_graph_node(data: dict[str, Any]) -> InviteGraphNode:
    node = InviteGraphNode(
        user_id=int(data["user_id"]),
        username=data["username"],
        degree=int(data["degree"]),
        invited_at=data.get("invited_at"),
    )
    children_data = data.get("children", []) or []
    node.children = [_deserialize_graph_node(child) for child in children_data]
    return node


def _serialize_ancestor(ancestor: InviteAncestor) -> dict[str, Any]:
    return {
        "user_id": ancestor.user_id,
        "username": ancestor.username,
        "degree": ancestor.degree,
        "invited_at": ancestor.invited_at,
    }


def _deserialize_ancestor(data: dict[str, Any]) -> InviteAncestor:
    return InviteAncestor(
        user_id=int(data["user_id"]),
        username=data["username"],
        degree=int(data["degree"]),
        invited_at=data.get("invited_at"),
    )
