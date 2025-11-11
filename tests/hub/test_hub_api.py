from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.hub.app import create_hub_app
from app.hub.config import reset_settings_cache
from app.sync import signing


@pytest.fixture()
def tmp_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_path = tmp_path / "hub_config.json"
    storage_dir = tmp_path / "store"
    monkeypatch.setenv("WB_HUB_CONFIG", str(config_path))
    monkeypatch.setenv("WB_SYNC_HOME", str(tmp_path / ".sync"))
    yield config_path, storage_dir
    reset_settings_cache()


def _write_config(config_path: Path, storage_dir: Path, token: str, public_key: str) -> None:
    config = {
        "storage_dir": str(storage_dir),
        "peers": [
            {"name": "alpha", "token": token, "public_key": public_key},
        ],
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _create_signed_bundle(tmp_path: Path) -> tuple[Path, signing.SigningKey]:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "users").mkdir()
    manifest = bundle_dir / signing.MANIFEST_FILENAME
    manifest.write_text("abc  users/user_1.sync.txt\n", encoding="utf-8")
    user_file = bundle_dir / "users" / "user_1.sync.txt"
    user_file.write_text("Entity: user\nID: 1\n\n", encoding="utf-8")
    key = signing.generate_keypair(force=True)
    signing.sign_bundle(bundle_dir, key)
    return bundle_dir, key


def _bundle_bytes(bundle_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in bundle_dir.rglob("*"):
            tar.add(path, arcname=path.relative_to(bundle_dir))
    buffer.seek(0)
    return buffer.getvalue()


def test_upload_and_status_flow(tmp_env: tuple[Path, Path]) -> None:
    config_path, storage_dir = tmp_env
    bundle_dir, key = _create_signed_bundle(config_path.parent)
    _write_config(config_path, storage_dir, token="secret-token", public_key=key.public_key_b64)
    reset_settings_cache()

    app = create_hub_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/sync/alpha/bundle",
        headers={"Authorization": "Bearer secret-token"},
        files={"bundle": ("bundle.tar.gz", _bundle_bytes(bundle_dir), "application/gzip")},
    )
    assert resp.status_code == 202, resp.text
    payload = resp.json()
    assert payload["peer"] == "alpha"
    assert payload["stored_files"] >= 3

    status_resp = client.get(
        "/api/v1/sync/alpha/status",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert status_resp.status_code == 200
    status_payload = status_resp.json()
    assert status_payload["has_bundle"] is True
    assert status_payload["metadata"]["manifest_digest"] == payload["manifest_digest"]

    download = client.get(
        "/api/v1/sync/alpha/bundle",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/gzip"
    with tarfile.open(fileobj=io.BytesIO(download.content), mode="r:gz") as tar:
        names = tar.getnames()
    assert signing.MANIFEST_FILENAME in names
    assert signing.SIGNATURE_FILENAME in names


def test_upload_rejects_invalid_signature(tmp_env: tuple[Path, Path]) -> None:
    config_path, storage_dir = tmp_env
    bundle_dir, key = _create_signed_bundle(config_path.parent)
    _write_config(config_path, storage_dir, token="token", public_key="WRONGKEY==")
    reset_settings_cache()

    app = create_hub_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/sync/alpha/bundle",
        headers={"Authorization": "Bearer token"},
        files={"bundle": ("bundle.tar.gz", _bundle_bytes(bundle_dir), "application/gzip")},
    )
    assert resp.status_code == 400
    assert "public key" in resp.json()["detail"].lower()
