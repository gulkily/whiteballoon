from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import InviteMapCache, User


class _SessionFactory:
    def __init__(self) -> None:
        self._engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(self._engine)

    def __call__(self) -> Session:
        return Session(self._engine)


_session_factory = _SessionFactory()


def test_invite_map_cache_round_trip() -> None:
    with _session_factory() as session:
        user = User(username="invite-cache-tester")
        session.add(user)
        session.commit()
        session.refresh(user)

        entry = InviteMapCache(
            user_id=user.id,
            payload="{\"root\":{}}",
            version="v1",
            generated_at=datetime.utcnow() - timedelta(minutes=5),
        )
        session.add(entry)
        session.commit()

        stored = session.get(InviteMapCache, user.id)
        assert stored is not None
        assert stored.user_id == user.id
        assert stored.payload.startswith("{")
        assert stored.version == "v1"
        assert stored.generated_at <= datetime.utcnow()
