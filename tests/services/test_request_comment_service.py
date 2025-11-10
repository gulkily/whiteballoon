from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import HelpRequest, User
from app.services import request_comment_service


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def create_user(session: Session, username: str) -> User:
    user = User(username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_request(session: Session, user: User) -> HelpRequest:
    help_request = HelpRequest(description="Need help", created_by_user_id=user.id)
    session.add(help_request)
    session.commit()
    session.refresh(help_request)
    return help_request


def test_add_and_list_comments(session: Session) -> None:
    author = create_user(session, "author")
    request = create_request(session, author)

    comment = request_comment_service.add_comment(
        session,
        help_request_id=request.id,
        user_id=author.id,
        body=" First! ",
    )

    assert comment.body == "First!"

    rows = request_comment_service.list_comments(session, help_request_id=request.id)
    assert len(rows) == 1
    stored_comment, stored_user = rows[0]
    assert stored_comment.id == comment.id
    assert stored_user.id == author.id


def test_add_comment_validates_body(session: Session) -> None:
    author = create_user(session, "author")
    request = create_request(session, author)

    with pytest.raises(ValueError):
        request_comment_service.add_comment(
            session,
            help_request_id=request.id,
            user_id=author.id,
            body="   ",
        )

    with pytest.raises(ValueError):
        request_comment_service.add_comment(
            session,
            help_request_id=request.id,
            user_id=author.id,
            body="x" * (request_comment_service.MAX_COMMENT_LENGTH + 1),
        )
