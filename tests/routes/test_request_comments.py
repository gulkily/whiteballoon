from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import create_app
from app.models import HelpRequest, RequestComment, User, UserSession
from app.services.auth_service import SESSION_COOKIE_NAME


def build_app_and_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = create_app()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    return app, engine


def create_user_with_session(engine, *, username="member", fully_authenticated=True):
    with Session(engine) as session:
        user = User(username=username)
        session.add(user)
        session.commit()
        session.refresh(user)

        session_record = UserSession(user_id=user.id, is_fully_authenticated=fully_authenticated)
        session.add(session_record)
        session.commit()
        session.refresh(session_record)

        request = HelpRequest(description="Need assistance", created_by_user_id=user.id)
        session.add(request)
        session.commit()
        session.refresh(request)

        return user.id, session_record.id, request.id


def test_create_comment_returns_json():
    app, engine = build_app_and_engine()
    client = TestClient(app)
    user_id, session_id, request_id = create_user_with_session(engine)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers={"X-Requested-With": "Fetch", "Accept": "application/json"},
        data={"body": "Appreciate the update"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "comment" in data

    with Session(engine) as session:
        stored = session.exec(
            select(RequestComment).where(RequestComment.help_request_id == request_id)
        ).all()
        assert len(stored) == 1

    app.dependency_overrides.clear()


def test_create_comment_validates_body():
    app, engine = build_app_and_engine()
    client = TestClient(app)
    _, session_id, request_id = create_user_with_session(engine)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers={"X-Requested-With": "Fetch", "Accept": "application/json"},
        data={"body": "   "},
    )

    assert response.status_code == 422
    data = response.json()
    assert "errors" in data

    app.dependency_overrides.clear()


def test_create_comment_requires_full_auth():
    app, engine = build_app_and_engine()
    client = TestClient(app)
    _, session_id, request_id = create_user_with_session(engine, fully_authenticated=False)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)

    response = client.post(
        f"/requests/{request_id}/comments",
        headers={"X-Requested-With": "Fetch", "Accept": "application/json"},
        data={"body": "Message"},
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()
