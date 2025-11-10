from __future__ import annotations

from fastapi.testclient import TestClient
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import create_app
from app.models import User, UserAttribute, UserSession
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


def test_account_settings_uploads_photo(tmp_path=None) -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    user_id, session_id = _create_user_with_session(engine)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    photo_bytes = b"png-data"
    response = client.post(
        "/settings/account",
        data={"contact_email": "member@example.com"},
        files={"profile_photo": ("avatar.png", photo_bytes, "image/png")},
    )

    assert response.status_code == 200
    assert "Account details updated" in response.text

    with Session(engine) as session:
        attribute = session.exec(
            select(UserAttribute).where(
                UserAttribute.user_id == user_id,
                UserAttribute.key == "profile_photo_url",
            )
        ).first()
        assert attribute is not None
        assert attribute.value and attribute.value.startswith("/static/uploads/profile_photos/")
        stored_path = Path(attribute.value.lstrip("/"))
        assert stored_path.exists()
        stored_path.unlink(missing_ok=True)

    app.dependency_overrides.clear()


def test_account_settings_can_remove_photo() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    user_id, session_id = _create_user_with_session(engine)

    with Session(engine) as session:
        session.add(
            UserAttribute(
                user_id=user_id,
                key="profile_photo_url",
                value="/static/uploads/profile_photos/existing.png",
            )
        )
        session.commit()

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.post(
        "/settings/account",
        data={"contact_email": "member@example.com", "remove_photo": "1"},
    )

    assert response.status_code == 200

    with Session(engine) as session:
        attribute = session.exec(
            select(UserAttribute).where(
                UserAttribute.user_id == user_id,
                UserAttribute.key == "profile_photo_url",
            )
        ).first()
        assert attribute is None

    app.dependency_overrides.clear()
