from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.hub.app import create_hub_app
from app.hub.config import hash_token, reset_settings_cache
from app.hub.storage import METADATA_FILENAME


@pytest.fixture()
def tmp_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_path = tmp_path / "hub_config.json"
    storage_dir = tmp_path / "store"
    monkeypatch.setenv("WB_HUB_CONFIG", str(config_path))
    yield config_path, storage_dir
    reset_settings_cache()


def _write_config(config_path: Path, storage_dir: Path, *, admin_token: str | None = None) -> None:
    config = {
        "storage_dir": str(storage_dir),
        "peers": [
            {
                "name": "alpha",
                "token_hash": hash_token("peer-token"),
                "public_key": "BASE64KEY",
            }
        ],
    }
    if admin_token:
        config["admin_tokens"] = [
            {
                "name": "ops",
                "token_hash": hash_token(admin_token),
            }
        ]
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _seed_bundle(storage_dir: Path, peer: str) -> None:
    peer_dir = storage_dir / peer
    (peer_dir / "users").mkdir(parents=True, exist_ok=True)
    (peer_dir / "users" / "user.sync.txt").write_text("Entity: user\nID: 1\n", encoding="utf-8")
    (peer_dir / "manifest.sync.txt").write_text("abc  users/user.sync.txt\n", encoding="utf-8")
    metadata = {
        "peer": peer,
        "manifest_digest": "abc123",
        "signed_at": "2024-01-01T00:00:00+00:00",
    }
    (peer_dir / METADATA_FILENAME).write_text(json.dumps(metadata), encoding="utf-8")


def test_admin_disabled_without_tokens(tmp_env: tuple[Path, Path]) -> None:
    config_path, storage_dir = tmp_env
    _write_config(config_path, storage_dir, admin_token=None)
    app = create_hub_app()
    client = TestClient(app)

    resp = client.get("/admin")
    assert resp.status_code == 200
    assert "Admin dashboard locked" in resp.text


def test_admin_login_and_dashboard(tmp_env: tuple[Path, Path]) -> None:
    config_path, storage_dir = tmp_env
    secret = "admin-secret"
    _write_config(config_path, storage_dir, admin_token=secret)
    _seed_bundle(storage_dir, "alpha")
    app = create_hub_app()
    client = TestClient(app)

    landing = client.get("/admin")
    assert landing.status_code == 200
    assert "Access token" in landing.text

    auth = client.post("/admin/login", data={"token": secret}, allow_redirects=False)
    assert auth.status_code == 303
    assert auth.headers["location"] == "/admin"

    dashboard = client.get("/admin")
    assert "Hub Control" in dashboard.text
    assert "alpha" in dashboard.text
    assert "abc123" in dashboard.text

    logout = client.post("/admin/logout", allow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/admin"
