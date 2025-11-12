from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import create_app
from app.models import User, UserSession
from app.security.csrf import generate_csrf_token
from app.services.auth_service import SESSION_COOKIE_NAME
from app.sync import job_tracker
from app.sync import activity_log
from app.sync.peers import Peer, save_peers


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


def _create_user_with_session(engine, *, is_admin: bool) -> tuple[int, str]:
    with Session(engine) as session:
        user = User(username="admin" if is_admin else "member", is_admin=is_admin)
        session.add(user)
        session.commit()
        session.refresh(user)

        session_record = UserSession(user_id=user.id, is_fully_authenticated=True)
        session.add(session_record)
        session.commit()
        session.refresh(session_record)

        return user.id, session_record.id


def _override_peer_file(monkeypatch, path: Path) -> Path:
    monkeypatch.setattr("app.sync.peers.PEER_FILE", path)
    return path


def test_sync_control_renders_for_admin(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.get("/admin/sync-control")

    assert response.status_code == 200
    assert "Sync Control Center" in response.text
    assert not peer_file.exists()

    app.dependency_overrides.clear()


def test_sync_control_rejects_non_admin(monkeypatch, tmp_path) -> None:
    _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=False)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    response = client.get("/admin/sync-control")

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_sync_control_add_peer_creates_entry(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)

    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    csrf_token = generate_csrf_token(session_id)
    response = client.post(
        "/admin/sync-control/peers/add",
        data={
            "name": "alpha",
            "path": "/data/alpha",
            "url": "",
            "token": "",
            "public_key": "",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 303
    saved = peer_file.read_text(encoding="utf-8")
    assert "name=alpha" in saved
    assert "path=/data/alpha" in saved

    app.dependency_overrides.clear()


def test_sync_control_edit_peer_updates_fields(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    save_peers([Peer(name="alpha", path=Path("/old"), url=None)], peer_file=peer_file)

    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)
    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    csrf_token = generate_csrf_token(session_id)

    response = client.post(
        "/admin/sync-control/peers/alpha/edit",
        data={
            "path": "",
            "url": "https://hub.example",
            "token": "secret",
            "public_key": "ABCDEF==",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 303
    updated = peer_file.read_text(encoding="utf-8")
    assert "url=https://hub.example" in updated
    assert "token=secret" in updated
    assert "public_key=ABCDEF==" in updated

    app.dependency_overrides.clear()


def test_sync_control_delete_peer(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    save_peers(
        [
            Peer(name="alpha", path=Path("/data/alpha")),
            Peer(name="beta", path=Path("/data/beta")),
        ],
        peer_file=peer_file,
    )

    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)
    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    csrf_token = generate_csrf_token(session_id)

    response = client.post(
        "/admin/sync-control/peers/alpha/delete",
        data={"csrf_token": csrf_token},
    )

    assert response.status_code == 303
    saved = peer_file.read_text(encoding="utf-8")
    assert "name=alpha" not in saved
    assert "name=beta" in saved

    app.dependency_overrides.clear()


def test_sync_control_push_queues_job(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    save_peers([Peer(name="alpha", path=Path("/data/alpha"))], peer_file=peer_file)

    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)
    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    csrf_token = generate_csrf_token(session_id)

    called: dict[str, str] = {}

    def fake_run(peer_name: str) -> None:
        called["peer"] = peer_name
        job_tracker.mark_finished(peer_name, "push", True, "done")

    monkeypatch.setattr("app.routes.ui._run_push_job", fake_run)

    response = client.post(
        "/admin/sync-control/peers/alpha/push",
        data={"csrf_token": csrf_token},
    )

    assert response.status_code == 303
    assert called.get("peer") == "alpha"
    snapshot = job_tracker.snapshot()
    assert "alpha" in snapshot and "push" in snapshot["alpha"]
    events = activity_log.read_events()
    assert events and events[0]["action"] == "push"

    app.dependency_overrides.clear()


def test_sync_control_pull_queues_job(monkeypatch, tmp_path) -> None:
    peer_file = _override_peer_file(monkeypatch, tmp_path / "peers.txt")
    save_peers([Peer(name="beta", path=Path("/data/beta"))], peer_file=peer_file)

    app, engine = _build_test_app()
    client = TestClient(app)
    _, session_id = _create_user_with_session(engine, is_admin=True)
    client.cookies.set(SESSION_COOKIE_NAME, session_id)
    csrf_token = generate_csrf_token(session_id)

    called: dict[str, tuple[str, bool]] = {}

    def fake_pull(peer_name: str, allow_unsigned: bool) -> None:
        called["args"] = (peer_name, allow_unsigned)
        job_tracker.mark_finished(peer_name, "pull", True, "done")

    monkeypatch.setattr("app.routes.ui._run_pull_job", fake_pull)

    response = client.post(
        "/admin/sync-control/peers/beta/pull",
        data={"csrf_token": csrf_token, "allow_unsigned": "1"},
    )

    assert response.status_code == 303
    assert called.get("args") == ("beta", True)
    snapshot = job_tracker.snapshot()
    assert "beta" in snapshot and "pull" in snapshot["beta"]
    events = activity_log.read_events()
    assert events and events[0]["action"] == "pull"

    app.dependency_overrides.clear()
@pytest.fixture(autouse=True)
def _reset_job_state():
    job_tracker.reset()
    activity_log.reset()
    yield
