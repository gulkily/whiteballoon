from __future__ import annotations

from pathlib import Path

import pytest

from app.sync import signing


def test_key_generation_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WB_SYNC_HOME", str(tmp_path / ".sync"))
    signing.remove_keys()
    key = signing.generate_keypair()
    assert key.public_key
    loaded = signing.load_keypair()
    assert loaded is not None
    assert loaded.key_id == key.key_id
    assert loaded.public_key == key.public_key


def test_sign_and_verify_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WB_SYNC_HOME", str(tmp_path / ".sync"))
    signing.remove_keys()
    key = signing.generate_keypair()

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    manifest = bundle_dir / signing.MANIFEST_FILENAME
    manifest.write_text("hash-me\n", encoding="utf-8")

    signing.sign_bundle(bundle_dir, key)
    meta = signing.verify_bundle_signature(bundle_dir, expected_public_key=key.public_key_b64)
    assert meta.key_id == key.key_id
    pub_file = bundle_dir / signing.PUBLIC_KEYS_DIRNAME / f"{key.key_id}.pub"
    assert pub_file.exists()
    contents = pub_file.read_text(encoding="utf-8")
    assert key.public_key_b64 in contents

    # Wrong peer key should raise
    with pytest.raises(signing.SignatureVerificationError):
        signing.verify_bundle_signature(bundle_dir, expected_public_key="ZmFrZS1rZXk=")

    # Tampering invalidates the signature
    manifest.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(signing.SignatureVerificationError):
        signing.verify_bundle_signature(bundle_dir, expected_public_key=key.public_key_b64)
