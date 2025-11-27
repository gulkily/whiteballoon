from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import create_app
from app.models import User, UserSession
from app.services import user_profile_highlight_service
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


def _create_user_with_session(engine, *, username: str, is_admin: bool) -> tuple[int, str]:
    with Session(engine) as session:
        user = User(username=username, is_admin=is_admin)
        session.add(user)
        session.commit()
        session.refresh(user)

        session_record = UserSession(user_id=user.id, is_fully_authenticated=True)
        session.add(session_record)
        session.commit()
        session.refresh(session_record)

        return user.id, session_record.id


def test_admin_profiles_requires_admin_access() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, username="member", is_admin=False)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.get("/admin/profiles")

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_admin_panel_links_render() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    _, admin_session_id = _create_user_with_session(engine, username="admin", is_admin=True)

    client.cookies.set(SESSION_COOKIE_NAME, admin_session_id)
    response = client.get("/admin")

    assert response.status_code == 200
    assert "/admin/profiles" in response.text
    assert "/sync/public" in response.text

    app.dependency_overrides.clear()


def test_admin_profiles_lists_users_with_filters() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    _, admin_session_id = _create_user_with_session(engine, username="admin", is_admin=True)

    with Session(engine) as session:
        session.add(User(username="delta", contact_email="delta@example.org"))
        session.add(User(username="echo", contact_email="echo@example.org"))
        session.commit()

    client.cookies.set(SESSION_COOKIE_NAME, admin_session_id)
    response = client.get("/admin/profiles", params={"username": "del"})

    assert response.status_code == 200
    assert "delta@example.org" in response.text
    assert "profile-name-link" in response.text
    assert "/admin/profiles/" in response.text
    assert "echo@example.org" not in response.text

    app.dependency_overrides.clear()


def test_admin_profile_detail_shows_highlight() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    target_user_id, _ = _create_user_with_session(engine, username="target", is_admin=False)
    _, admin_session_id = _create_user_with_session(engine, username="admin", is_admin=True)

    with Session(engine) as session:
        meta = user_profile_highlight_service.HighlightMeta(
            source_group="harvard",
            llm_model="test",
            snapshot_last_seen_at=datetime.utcnow(),
            guardrail_issues=[],
        )
        user_profile_highlight_service.upsert_auto(
            session,
            user_id=target_user_id,
            bio_paragraphs=["Connector"],
            proof_points=[],
            quotes=[],
            confidence_note="Based on test data",
            snapshot_hash="hash",
            meta=meta,
        )
        session.commit()

    client.cookies.set(SESSION_COOKIE_NAME, admin_session_id)
    response = client.get(f"/admin/profiles/{target_user_id}")

    assert response.status_code == 200
    assert "Signal profile highlight" in response.text
    assert "Connector" in response.text

    app.dependency_overrides.clear()


def test_admin_profile_highlight_override_action() -> None:
    app, engine = _build_test_app()
    client = TestClient(app)
    target_user_id, _ = _create_user_with_session(engine, username="target", is_admin=False)
    _, admin_session_id = _create_user_with_session(engine, username="admin", is_admin=True)

    client.cookies.set(SESSION_COOKIE_NAME, admin_session_id)
    response = client.post(
        f"/admin/profiles/{target_user_id}/highlight",
        data={"action": "override", "override_text": "Manual text"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    with Session(engine) as session:
        record = user_profile_highlight_service.get(session, target_user_id)
        assert record is not None
        assert record.manual_override is True
        assert record.override_text == "Manual text"

    app.dependency_overrides.clear()
