from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import HelpRequest, RequestComment, User


def create_engine_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


def create_user(session: Session, username: str) -> User:
    user = User(username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_request(session: Session, creator: User) -> HelpRequest:
    help_request = HelpRequest(description="Need help", created_by_user_id=creator.id)
    session.add(help_request)
    session.commit()
    session.refresh(help_request)
    return help_request


def test_request_comment_persists() -> None:
    engine = create_engine_session()
    with Session(engine) as session:
        author = create_user(session, "commenter")
        help_request = create_request(session, author)

        comment = RequestComment(help_request_id=help_request.id, user_id=author.id, body="Thanks")
        session.add(comment)
        session.commit()
        session.refresh(comment)

        assert comment.id is not None
        assert comment.created_at is not None
        assert comment.deleted_at is None

        stored = session.get(RequestComment, comment.id)
        assert stored is not None
        assert stored.body == "Thanks"
        assert stored.help_request_id == help_request.id
        assert stored.user_id == author.id
