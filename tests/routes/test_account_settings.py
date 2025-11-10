from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import create_app
from app.models import User, UserSession
from app.services.auth_service import SESSION_COOKIE_NAME


def _build_test_app():
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


def _create_user_with_session(engine) -> tuple[int, str]:
    with Session(engine) as session:
        user = User(username="member", contact_email="old@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)

        session_record = UserSession(user_id=user.id, is_fully_authenticated=True)
        session.add(session_record)
        session.commit()
        session.refresh(session_record)

        return user.id, session_record.id


def test_account_settings_updates_email() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    user_id, session_id = _create_user_with_session(engine)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.post("/settings/account", data={"contact_email": "new@example.com"})

    assert response.status_code == 200
    assert "Account details updated" in response.text

    with Session(engine) as session:
        updated = session.get(User, user_id)
        assert updated.contact_email == "new@example.com"

    app.dependency_overrides.clear()


def test_account_settings_rejects_invalid_email() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    user_id, session_id = _create_user_with_session(engine)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.post("/settings/account", data={"contact_email": "not-an-email"})

    assert response.status_code == 200
    assert "Enter a valid email address." in response.text

    with Session(engine) as session:
        user = session.get(User, user_id)
        assert user.contact_email == "old@example.com"

    app.dependency_overrides.clear()
