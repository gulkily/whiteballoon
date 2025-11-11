from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .config import HubPeer, HubSettings

METADATA_FILENAME = "hub_metadata.json"


def _peer_storage(settings: HubSettings, peer: HubPeer) -> Path:
    return settings.storage_dir / peer.name


def write_bundle(settings: HubSettings, peer: HubPeer, bundle_root: Path, metadata: dict[str, object]) -> None:
    target_dir = _peer_storage(settings, peer)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(bundle_root, target_dir)
    metadata_path = target_dir / METADATA_FILENAME
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str) + "\n", encoding="utf-8")


def read_metadata(settings: HubSettings, peer: HubPeer) -> dict[str, object] | None:
    target_dir = _peer_storage(settings, peer)
    metadata_path = target_dir / METADATA_FILENAME
    if metadata_path.exists():
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def bundle_exists(settings: HubSettings, peer: HubPeer) -> bool:
    target_dir = _peer_storage(settings, peer)
    return (target_dir / "manifest.sync.txt").exists()


def iter_bundle_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def summarize_bundle(root: Path) -> dict[str, object]:
    files = list(iter_bundle_files(root))
    total_bytes = sum(path.stat().st_size for path in files)
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
    }


def build_metadata(peer: HubPeer, manifest_digest: str, signed_at: datetime) -> dict[str, object]:
    return {
        "peer": peer.name,
        "manifest_digest": manifest_digest,
        "signed_at": signed_at.isoformat(),
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }


def get_bundle_path(settings: HubSettings, peer: HubPeer) -> Path:
    return _peer_storage(settings, peer)


__all__ = [
    "write_bundle",
    "read_metadata",
    "bundle_exists",
    "get_bundle_path",
    "summarize_bundle",
    "build_metadata",
    "METADATA_FILENAME",
]
