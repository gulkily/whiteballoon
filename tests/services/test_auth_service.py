from __future__ import annotations

import pytest
from pathlib import Path
import sys

from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import models  # noqa: F401
from app.models import User
from app.services import auth_service, user_attribute_service


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def create_user(session: Session, username: str) -> User:
    user = User(username=username, is_admin=False)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_create_user_with_invite_copies_photo(session: Session) -> None:
    inviter = create_user(session, "inviter")
    personalization = auth_service.InvitePersonalizationPayload(
        photo_url="https://example.org/photo.png",
        gratitude_note="",
        support_message="",
        help_examples=[],
        fun_details="",
    )
    invite_result = auth_service.create_invite_token(
        session,
        created_by=inviter,
        personalization=personalization,
    )

    registration = auth_service.create_user_with_invite(
        session,
        username="invitee",
        contact_email=None,
        invite_token=invite_result.invite.token,
    )

    stored = user_attribute_service.get_attribute(
        session,
        user_id=registration.user.id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )
    assert stored == "https://example.org/photo.png"


def test_create_user_without_photo_leaves_attribute_empty(session: Session) -> None:
    inviter = create_user(session, "inviter")
    invite_result = auth_service.create_invite_token(session, created_by=inviter)

    registration = auth_service.create_user_with_invite(
        session,
        username="invitee",
        contact_email=None,
        invite_token=invite_result.invite.token,
    )

    stored = user_attribute_service.get_attribute(
        session,
        user_id=registration.user.id,
        key=user_attribute_service.PROFILE_PHOTO_URL_KEY,
    )
    assert stored is None
