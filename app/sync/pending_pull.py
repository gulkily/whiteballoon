from __future__ import annotations

import json
import shutil
import tarfile
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session

from app.db import get_engine
from app.sync.export_import import import_sync_data
from app.sync.peers import Peer, load_peers, save_peers
from app.sync.signing import verify_bundle_signature

PENDING_PULL_ROOT = Path("data/pending_pull")


@dataclass
class PendingPullEntry:
    id: str
    peer_name: str
    presented_key: str
    manifest_digest: str | None
    signed_at: str | None
    created_at: datetime
    bundle_path: Path

    @property
    def directory(self) -> Path:
        return self.bundle_path.parent


def cache_pending_pull(
    *,
    peer_name: str,
    bundle_bytes: bytes,
    presented_key: str,
    manifest_digest: str,
    signed_at: datetime,
) -> PendingPullEntry:
    PENDING_PULL_ROOT.mkdir(parents=True, exist_ok=True)
    entry_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    entry_dir = PENDING_PULL_ROOT / peer_name / entry_id
    entry_dir.mkdir(parents=True, exist_ok=False)
    bundle_path = entry_dir / "bundle.tar.gz"
    bundle_path.write_bytes(bundle_bytes)
    created_at = datetime.now(timezone.utc)
    meta = {
        "peer": peer_name,
        "pending_id": entry_id,
        "presented_key": presented_key,
        "manifest_digest": manifest_digest,
        "signed_at": signed_at.isoformat(),
        "created_at": created_at.isoformat(),
    }
    (entry_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return PendingPullEntry(
        id=entry_id,
        peer_name=peer_name,
        presented_key=presented_key,
        manifest_digest=manifest_digest,
        signed_at=signed_at.isoformat(),
        created_at=created_at,
        bundle_path=bundle_path,
    )


def list_pending_pulls() -> list[PendingPullEntry]:
    if not PENDING_PULL_ROOT.exists():
        return []
    entries: list[PendingPullEntry] = []
    for peer_dir in PENDING_PULL_ROOT.iterdir():
        if not peer_dir.is_dir():
            continue
        for entry_dir in peer_dir.iterdir():
            if not entry_dir.is_dir():
                continue
            entry = _load_entry(peer_dir.name, entry_dir)
            if entry:
                entries.append(entry)
    return sorted(entries, key=lambda entry: entry.created_at, reverse=True)


def get_pending_pull(pending_id: str) -> PendingPullEntry | None:
    if not PENDING_PULL_ROOT.exists():
        return None
    for peer_dir in PENDING_PULL_ROOT.iterdir():
        entry_dir = peer_dir / pending_id
        if entry_dir.exists():
            return _load_entry(peer_dir.name, entry_dir)
    return None


def remove_pending_pull(entry: PendingPullEntry) -> None:
    if entry.directory.exists():
        shutil.rmtree(entry.directory, ignore_errors=True)
    peer_dir = entry.directory.parent
    if peer_dir.exists():
        try:
            next(peer_dir.iterdir())
        except StopIteration:
            shutil.rmtree(peer_dir, ignore_errors=True)


def approve_pending_pull(entry: PendingPullEntry) -> tuple[str, int, bool]:
    peers = load_peers()
    updated: list[Peer] = []
    target: Peer | None = None
    key_updated = False
    for peer in peers:
        if peer.name == entry.peer_name:
            if peer.public_key != entry.presented_key:
                peer = Peer(
                    name=peer.name,
                    path=peer.path,
                    url=peer.url,
                    token=peer.token,
                    public_key=entry.presented_key,
                )
                key_updated = True
            target = peer
        updated.append(peer)
    if target is None:
        raise ValueError(f"Peer '{entry.peer_name}' not found in local registry.")
    save_peers(updated)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bundle_dir = tmp_path / "bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(entry.bundle_path, "r:gz") as tar:
            tar.extractall(path=bundle_dir)
        verify_bundle_signature(bundle_dir, expected_public_key=entry.presented_key)
        engine = get_engine()
        with Session(engine) as session:
            count = import_sync_data(session, bundle_dir)
    remove_pending_pull(entry)
    return target.name, count, key_updated


def _load_entry(peer_name: str, entry_dir: Path) -> PendingPullEntry | None:
    meta_path = entry_dir / "meta.json"
    bundle_path = entry_dir / "bundle.tar.gz"
    if not meta_path.exists() or not bundle_path.exists():
        return None
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    created_at = _parse_datetime(data.get("created_at")) or datetime.now(timezone.utc)
    return PendingPullEntry(
        id=str(data.get("pending_id") or entry_dir.name),
        peer_name=data.get("peer") or peer_name,
        presented_key=data.get("presented_key") or "",
        manifest_digest=data.get("manifest_digest"),
        signed_at=data.get("signed_at"),
        created_at=created_at,
        bundle_path=bundle_path,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
