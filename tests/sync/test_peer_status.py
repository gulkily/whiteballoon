from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.sync.peer_status import collect_peer_statuses
from app.sync.signing import generate_keypair, sign_bundle


@pytest.fixture(autouse=True)
def _sync_home(tmp_path, monkeypatch):
    sync_home = tmp_path / "sync-home"
    monkeypatch.setenv("WB_SYNC_HOME", str(sync_home))
    # Ensure directory exists for key generation
    (sync_home / "keys").mkdir(parents=True, exist_ok=True)
    yield
    monkeypatch.delenv("WB_SYNC_HOME", raising=False)


def _write_peer_file(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def test_collect_peer_statuses_handles_missing_path(tmp_path):
    peer_file = tmp_path / "peers.txt"
    _write_peer_file(
        peer_file,
        """
        [peer]
        name=alpha
        path=/does/not/exist
        """,
    )

    statuses = collect_peer_statuses(peer_file=peer_file)
    assert len(statuses) == 1
    status = statuses[0]
    assert status["status_label"] == "Path missing"
    assert status["status_tone"] == "danger"


def test_collect_peer_statuses_reports_filesystem_metadata(tmp_path):
    peer_file = tmp_path / "peers.txt"
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    manifest = bundle_dir / "manifest.sync.txt"
    manifest.write_text("sample manifest\n", encoding="utf-8")

    key = generate_keypair(force=True)
    sign_bundle(bundle_dir, key)

    _write_peer_file(
        peer_file,
        f"""
        [peer]
        name=alpha
        path={bundle_dir}
        """,
    )

    statuses = collect_peer_statuses(peer_file=peer_file)
    assert len(statuses) == 1
    status = statuses[0]
    assert status["status_label"] == "Bundle verified"
    assert status["status_tone"] == "success"
    assert status["public_key_hint"] == key.key_id
    assert status["manifest_digest"] is not None


def test_collect_peer_statuses_merges_hub_status(tmp_path, monkeypatch):
    peer_file = tmp_path / "peers.txt"
    _write_peer_file(
        peer_file,
        """
        [peer]
        name=hub-alpha
        url=https://hub.example
        token=secret-token
        public_key=BASE64KEY
        """,
    )

    # Ensure signing key exists for header generation
    generate_keypair(force=True)

    response_payload = {
        "has_bundle": True,
        "file_count": 12,
        "total_bytes": 4096,
        "metadata": {"signed_at": "2024-10-10T10:00:00Z", "manifest_digest": "abcd1234"},
    }

    def fake_request(url: str, *, headers: dict[str, str], timeout: float) -> httpx.Response:
        assert url.endswith("/api/v1/sync/hub-alpha/status")
        assert headers["Authorization"] == "Bearer secret-token"
        assert "X-WB-Public-Key" in headers
        return httpx.Response(status_code=200, content=json.dumps(response_payload).encode("utf-8"), headers={"content-type": "application/json"})

    monkeypatch.setattr("app.sync.peer_status._perform_hub_request", fake_request)

    statuses = collect_peer_statuses(peer_file=peer_file)
    assert len(statuses) == 1
    status = statuses[0]
    assert status["status_label"] == "Bundle ready"
    assert status["status_tone"] == "success"
    assert status["file_count"] == 12
    assert status["total_bytes"] == 4096
    assert status["manifest_digest_short"] == "abcd1234"
