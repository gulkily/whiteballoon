from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

SIGNATURE_VERSION = "1"
MANIFEST_FILENAME = "manifest.sync.txt"
SIGNATURE_FILENAME = "bundle.sig"
PUBLIC_KEYS_DIRNAME = "public_keys"
SYNC_ROOT_ENV = "WB_SYNC_HOME"


@dataclass
class SigningKey:
    key_id: str
    public_key: bytes
    private_key: ed25519.Ed25519PrivateKey
    created_at: Optional[datetime] = None

    @property
    def public_key_b64(self) -> str:
        return b64encode(self.public_key).decode("ascii")


@dataclass
class SignatureMetadata:
    key_id: str
    public_key_b64: str
    manifest_digest: str
    signed_at: datetime
    signature_b64: str


class SignatureVerificationError(RuntimeError):
    """Raised when bundle signature validation fails."""


# ---- Paths -----------------------------------------------------------------

def _sync_root() -> Path:
    env = os.environ.get(SYNC_ROOT_ENV)
    if env:
        return Path(env)
    return Path(".sync")


def _keys_dir() -> Path:
    return _sync_root() / "keys"


def _private_key_path() -> Path:
    return _keys_dir() / "id_ed25519"


def _public_key_path() -> Path:
    return _keys_dir() / "id_ed25519.pub"


def _metadata_path() -> Path:
    return _keys_dir() / "key_metadata.json"


# ---- Key Management --------------------------------------------------------

def keypair_exists() -> bool:
    return _private_key_path().exists() and _public_key_path().exists()


def _compute_key_id(public_key: bytes) -> str:
    digest = hashlib.sha256(public_key).hexdigest()
    return digest[:16]


def _write_metadata(key_id: str, created_at: datetime) -> None:
    data = {"key_id": key_id, "created_at": created_at.isoformat()}
    _metadata_path().write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _read_metadata() -> tuple[Optional[str], Optional[datetime]]:
    path = _metadata_path()
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, None
    key_id = data.get("key_id")
    created_at_raw = data.get("created_at")
    created_at = None
    if isinstance(created_at_raw, str):
        try:
            created_at = datetime.fromisoformat(created_at_raw)
        except ValueError:
            created_at = None
    return key_id, created_at


def generate_keypair(force: bool = False) -> SigningKey:
    keys_dir = _keys_dir()
    keys_dir.mkdir(parents=True, exist_ok=True)
    if keypair_exists() and not force:
        raise FileExistsError("Signing key already exists; use force=True to regenerate")

    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    _private_key_path().write_text(b64encode(private_bytes).decode("ascii") + "\n", encoding="utf-8")
    _public_key_path().write_text(b64encode(public_bytes).decode("ascii") + "\n", encoding="utf-8")

    key_id = _compute_key_id(public_bytes)
    created_at = datetime.now(timezone.utc)
    _write_metadata(key_id, created_at)
    return SigningKey(key_id=key_id, public_key=public_bytes, private_key=private_key, created_at=created_at)


def load_keypair() -> Optional[SigningKey]:
    if not keypair_exists():
        return None
    private_text = _private_key_path().read_text(encoding="utf-8").strip()
    public_text = _public_key_path().read_text(encoding="utf-8").strip()
    if not private_text or not public_text:
        return None
    private_bytes = b64decode(private_text)
    public_bytes = b64decode(public_text)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
    # Ensure public key matches stored private key
    derived_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if derived_public != public_bytes:
        raise ValueError("Stored public/private key mismatch")
    key_id_meta, created_at = _read_metadata()
    key_id = key_id_meta or _compute_key_id(public_bytes)
    return SigningKey(key_id=key_id, public_key=public_bytes, private_key=private_key, created_at=created_at)


def ensure_local_keypair(auto_generate: bool = True) -> tuple[Optional[SigningKey], bool]:
    existing = load_keypair()
    if existing:
        return existing, False
    if not auto_generate:
        return None, False
    created = generate_keypair(force=False)
    return created, True


# ---- Signing Helpers -------------------------------------------------------

def _read_signature_headers(sig_path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    with sig_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
    return headers


def sign_bundle(bundle_dir: Path, keypair: SigningKey) -> Path:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest_bytes = manifest_path.read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    signature = keypair.private_key.sign(manifest_bytes)

    sig_path = bundle_dir / SIGNATURE_FILENAME
    signed_at = datetime.now(timezone.utc).isoformat()
    headers = {
        "Signature-Version": SIGNATURE_VERSION,
        "Key-ID": keypair.key_id,
        "Public-Key": keypair.public_key_b64,
        "Manifest-Digest": digest,
        "Signed-At": signed_at,
        "Signature": b64encode(signature).decode("ascii"),
    }
    with sig_path.open("w", encoding="utf-8") as handle:
        for key, value in headers.items():
            handle.write(f"{key}: {value}\n")
    keys_dir = bundle_dir / PUBLIC_KEYS_DIRNAME
    keys_dir.mkdir(parents=True, exist_ok=True)
    pub_path = keys_dir / f"{keypair.key_id}.pub"
    payload = f"Key-ID: {keypair.key_id}\nPublic-Key: {keypair.public_key_b64}\n"
    current = pub_path.read_text(encoding="utf-8") if pub_path.exists() else None
    if current != payload:
        pub_path.write_text(payload, encoding="utf-8")
    return sig_path


def _normalize_public_key(value: str | None) -> str | None:
    if value is None:
        return None
    return "".join(value.split())


def verify_bundle_signature(bundle_dir: Path, expected_public_key: str | None = None) -> SignatureMetadata:
    sig_path = bundle_dir / SIGNATURE_FILENAME
    if not sig_path.exists():
        raise SignatureVerificationError(f"Signature file missing: {sig_path}")
    headers = _read_signature_headers(sig_path)
    required = ["Signature-Version", "Public-Key", "Signature", "Manifest-Digest", "Signed-At"]
    for key in required:
        if key not in headers:
            raise SignatureVerificationError(f"Signature file missing '{key}' header")
    if headers["Signature-Version"] != SIGNATURE_VERSION:
        raise SignatureVerificationError(
            f"Unsupported signature version: {headers['Signature-Version']} (expected {SIGNATURE_VERSION})"
        )

    manifest_path = bundle_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise SignatureVerificationError(f"Manifest not found for signature: {manifest_path}")
    manifest_bytes = manifest_path.read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    if digest != headers["Manifest-Digest"]:
        raise SignatureVerificationError("Manifest digest mismatch")

    public_key_b64 = _normalize_public_key(headers["Public-Key"])
    signature_b64 = headers["Signature"]
    try:
        public_bytes = b64decode(public_key_b64)
        signature_bytes = b64decode(signature_b64)
    except Exception as exc:  # noqa: BLE001 - want original message suppressed
        raise SignatureVerificationError("Failed to decode signature payload") from exc

    expected_normalized = _normalize_public_key(expected_public_key)
    if expected_normalized and expected_normalized != public_key_b64:
        raise SignatureVerificationError("Signature public key does not match expected peer key")

    public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
    try:
        public_key.verify(signature_bytes, manifest_bytes)
    except InvalidSignature as exc:  # pragma: no cover - cryptography-specific path
        raise SignatureVerificationError("Bundle signature verification failed") from exc

    try:
        signed_at = datetime.fromisoformat(headers["Signed-At"])
    except ValueError:
        signed_at = datetime.now(timezone.utc)

    key_id = headers.get("Key-ID") or _compute_key_id(public_bytes)
    return SignatureMetadata(
        key_id=key_id,
        public_key_b64=public_key_b64,
        manifest_digest=digest,
        signed_at=signed_at,
        signature_b64=signature_b64,
    )


def remove_keys() -> None:
    """Dangerous helper used only for forced regeneration/tests."""
    for path in (_private_key_path(), _public_key_path(), _metadata_path()):
        if path.exists():
            path.unlink()
