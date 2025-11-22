from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

PENDING_ROOT = Path(os.environ.get("WB_HUB_PENDING_DIR", "data/hub_pending"))
METADATA_FILENAME = "metadata.json"
BUNDLE_FILENAME = "bundle.tar.gz"


@dataclass(frozen=True)
class PendingKeyApproval:
    id: str
    peer_name: str
    presented_key: str
    bundle_path: Path
    created_at: datetime
    manifest_digest: str | None = None
    signed_at: datetime | None = None


def _entry_dir(peer_name: str, entry_id: str) -> Path:
    return PENDING_ROOT / peer_name / entry_id


def queue_pending_key(
    *,
    peer_name: str,
    presented_key: str,
    bundle_source: Path,
    manifest_digest: str | None = None,
    signed_at: datetime | None = None,
) -> PendingKeyApproval:
    PENDING_ROOT.mkdir(parents=True, exist_ok=True)
    entry_id = f"{int(datetime.now(timezone.utc).timestamp())}-{uuid4().hex[:8]}"
    entry_dir = _entry_dir(peer_name, entry_id)
    entry_dir.mkdir(parents=True, exist_ok=False)

    bundle_target = entry_dir / BUNDLE_FILENAME
    shutil.copy2(bundle_source, bundle_target)

    created_at = datetime.now(timezone.utc)
    metadata = {
        "id": entry_id,
        "peer_name": peer_name,
        "presented_key": presented_key,
        "created_at": created_at.isoformat(),
        "manifest_digest": manifest_digest,
        "signed_at": signed_at.isoformat() if signed_at else None,
    }
    (entry_dir / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return PendingKeyApproval(
        id=entry_id,
        peer_name=peer_name,
        presented_key=presented_key,
        bundle_path=bundle_target,
        created_at=created_at,
        manifest_digest=manifest_digest,
        signed_at=signed_at,
    )


def list_pending_keys(peer_name: str | None = None) -> list[PendingKeyApproval]:
    if not PENDING_ROOT.exists():
        return []
    results: list[PendingKeyApproval] = []
    peers: Iterable[Path]
    if peer_name:
        peers = [PENDING_ROOT / peer_name]
    else:
        peers = (path for path in PENDING_ROOT.iterdir() if path.is_dir())
    for peer_dir in peers:
        if not peer_dir.exists():
            continue
        for entry_dir in sorted(peer_dir.iterdir()):
            if not entry_dir.is_dir():
                continue
            metadata_path = entry_dir / METADATA_FILENAME
            bundle_path = entry_dir / BUNDLE_FILENAME
            if not metadata_path.exists() or not bundle_path.exists():
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            created_at = _parse_datetime(data.get("created_at")) or datetime.fromtimestamp(0, tz=timezone.utc)
            signed_at = _parse_datetime(data.get("signed_at"))
            results.append(
                PendingKeyApproval(
                    id=str(data.get("id")),
                    peer_name=data.get("peer_name") or peer_dir.name,
                    presented_key=data.get("presented_key") or "",
                    bundle_path=bundle_path,
                    created_at=created_at,
                    manifest_digest=data.get("manifest_digest"),
                    signed_at=signed_at,
                )
            )
    return sorted(results, key=lambda item: item.created_at, reverse=True)


def get_pending_key(entry_id: str) -> PendingKeyApproval | None:
    if not PENDING_ROOT.exists():
        return None
    for peer_dir in PENDING_ROOT.iterdir():
        metadata_path = peer_dir / entry_id / METADATA_FILENAME
        bundle_path = peer_dir / entry_id / BUNDLE_FILENAME
        if metadata_path.exists() and bundle_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
            created_at = _parse_datetime(data.get("created_at")) or datetime.now(timezone.utc)
            signed_at = _parse_datetime(data.get("signed_at"))
            return PendingKeyApproval(
                id=str(data.get("id")),
                peer_name=data.get("peer_name") or peer_dir.name,
                presented_key=data.get("presented_key") or "",
                bundle_path=bundle_path,
                created_at=created_at,
                manifest_digest=data.get("manifest_digest"),
                signed_at=signed_at,
            )
    return None


def remove_pending_key(entry_id: str) -> None:
    if not PENDING_ROOT.exists():
        return
    for peer_dir in PENDING_ROOT.iterdir():
        entry_dir = peer_dir / entry_id
        if entry_dir.exists():
            shutil.rmtree(entry_dir, ignore_errors=True)
            # Clean up peer dir if empty
            try:
                next(peer_dir.iterdir())
            except StopIteration:
                shutil.rmtree(peer_dir, ignore_errors=True)
            break


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if not dt.tzinfo:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


__all__ = [
    "PendingKeyApproval",
    "queue_pending_key",
    "list_pending_keys",
    "get_pending_key",
    "remove_pending_key",
    "PENDING_ROOT",
]
