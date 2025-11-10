from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import User
from app.services import invite_graph_service, invite_map_cache_service


@pytest.fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _basic_invite_map(user: User) -> invite_graph_service.InviteMapPayload:
    root = invite_graph_service.InviteGraphNode(
        user_id=user.id,
        username=user.username,
        degree=0,
    )
    return invite_graph_service.InviteMapPayload(root=root, upstream=[])


def _create_user(session: Session, username: str) -> User:
    user = User(username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_store_and_get_cached_map(session: Session) -> None:
    user = _create_user(session, "cached-user")
    payload = _basic_invite_map(user)

    invite_map_cache_service.store_cached_map(session, user_id=user.id, invite_map=payload)
    cached = invite_map_cache_service.get_cached_map(session, user_id=user.id)

    assert cached is not None
    assert cached.root.user_id == user.id
    assert cached.upstream == []


def test_cached_map_expires_after_ttl(session: Session) -> None:
    user = _create_user(session, "expired-user")
    payload = _basic_invite_map(user)

    record = invite_map_cache_service.store_cached_map(
        session,
        user_id=user.id,
        invite_map=payload,
    )

    record.generated_at = datetime.utcnow() - timedelta(seconds=invite_map_cache_service.CACHE_TTL_SECONDS + 5)
    session.add(record)
    session.commit()

    assert invite_map_cache_service.get_cached_map(session, user_id=user.id) is None


def test_invalidate_cache_removes_entry(session: Session) -> None:
    user = _create_user(session, "invalidate-user")
    payload = _basic_invite_map(user)

    invite_map_cache_service.store_cached_map(session, user_id=user.id, invite_map=payload)
    invite_map_cache_service.invalidate_cache(session, user_id=user.id)

    assert invite_map_cache_service.get_cached_map(session, user_id=user.id) is None
