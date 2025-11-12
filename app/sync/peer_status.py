from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Optional

import httpx

from app.sync.peers import Peer, load_peers
from app.sync.signing import (
    SignatureVerificationError,
    ensure_local_keypair,
    verify_bundle_signature,
)

logger = logging.getLogger(__name__)
DEFAULT_STATUS_TIMEOUT = 5.0


@dataclass
class PeerStatus:
    name: str
    peer_kind: str
    peer_kind_label: str
    location: str
    location_label: str
    is_hub: bool
    public_key_hint: str | None
    status_label: str
    status_tone: str
    detail: str | None
    detail_tone: str
    signed_at: str | None
    manifest_digest: str | None
    manifest_digest_short: str | None
    file_count: int | None
    total_bytes: int | None
    has_bundle: bool | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "peer_kind": self.peer_kind,
            "peer_kind_label": self.peer_kind_label,
            "location": self.location,
            "location_label": self.location_label,
            "is_hub": self.is_hub,
            "public_key_hint": self.public_key_hint,
            "status_label": self.status_label,
            "status_tone": self.status_tone,
            "detail": self.detail,
            "detail_tone": self.detail_tone,
            "signed_at": self.signed_at,
            "manifest_digest": self.manifest_digest,
            "manifest_digest_short": self.manifest_digest_short,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "has_bundle": self.has_bundle,
        }


def collect_peer_statuses(
    *, peer_file: Path | None = None, status_timeout: float = DEFAULT_STATUS_TIMEOUT
) -> list[dict[str, Any]]:
    try:
        peers = load_peers(peer_file)
    except Exception as exc:  # noqa: BLE001 - want to log original reason
        logger.warning("Unable to load peers: %s", exc)
        return []

    statuses: list[PeerStatus] = []
    for peer in peers:
        if peer.url:
            statuses.append(_hub_peer_status(peer, status_timeout))
        else:
            statuses.append(_filesystem_peer_status(peer))

    statuses.sort(key=lambda item: item.name.lower())
    return [status.as_dict() for status in statuses]


def _filesystem_peer_status(peer: Peer) -> PeerStatus:
    if not peer.path:
        return PeerStatus(
            name=peer.name,
            peer_kind="filesystem",
            peer_kind_label="Filesystem peer",
            location="—",
            location_label="Bundle path",
            is_hub=False,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Not configured",
            status_tone="danger",
            detail="Peer entry is missing a filesystem path.",
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=False,
        )

    path = Path(peer.path).expanduser()
    location = str(path)
    if not path.exists():
        return PeerStatus(
            name=peer.name,
            peer_kind="filesystem",
            peer_kind_label="Filesystem peer",
            location=location,
            location_label="Bundle path",
            is_hub=False,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Path missing",
            status_tone="danger",
            detail=f"Directory not found: {location}",
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=False,
        )

    try:
        metadata = verify_bundle_signature(path)
    except SignatureVerificationError as exc:
        label, tone = _classify_signature_error(str(exc))
        return PeerStatus(
            name=peer.name,
            peer_kind="filesystem",
            peer_kind_label="Filesystem peer",
            location=location,
            location_label="Bundle path",
            is_hub=False,
            public_key_hint=_format_public_key(peer.public_key),
            status_label=label,
            status_tone=tone,
            detail=str(exc),
            detail_tone=tone,
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=False,
        )
    except OSError as exc:  # pragma: no cover - filesystem edge cases
        message = exc.strerror or str(exc)
        return PeerStatus(
            name=peer.name,
            peer_kind="filesystem",
            peer_kind_label="Filesystem peer",
            location=location,
            location_label="Bundle path",
            is_hub=False,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Read error",
            status_tone="danger",
            detail=message,
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=False,
        )

    signed_at = _normalize_datetime(metadata.signed_at)
    digest = metadata.manifest_digest
    digest_short = _shorten_hex(digest)
    key_hint = _format_public_key(peer.public_key) or metadata.key_id

    return PeerStatus(
        name=peer.name,
        peer_kind="filesystem",
        peer_kind_label="Filesystem peer",
        location=location,
        location_label="Bundle path",
        is_hub=False,
        public_key_hint=key_hint,
        status_label="Bundle verified",
        status_tone="success",
        detail=f"Signed with key {metadata.key_id}",
        detail_tone="muted",
        signed_at=signed_at,
        manifest_digest=digest,
        manifest_digest_short=digest_short,
        file_count=None,
        total_bytes=None,
        has_bundle=True,
    )


def _hub_peer_status(peer: Peer, timeout: float) -> PeerStatus:
    location = peer.url or "—"
    if not peer.token:
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Token required",
            status_tone="warning",
            detail="Add a bearer token to sync_peers.txt to contact this hub.",
            detail_tone="warning",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    try:
        signing_key, _ = ensure_local_keypair(auto_generate=True)
    except Exception as exc:  # noqa: BLE001 - propagate readable error
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Signing key error",
            status_tone="danger",
            detail=str(exc),
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    if not signing_key:
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Signing key missing",
            status_tone="danger",
            detail="Generate a local signing key before contacting hubs (wb sync keygen).",
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    headers = {
        "Authorization": f"Bearer {peer.token}",
        "X-WB-Public-Key": signing_key.public_key_b64,
    }
    url = _build_hub_status_url(peer)

    try:
        response = _perform_hub_request(url, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Hub unreachable",
            status_tone="danger",
            detail=str(exc),
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    if response.status_code >= 400:
        detail = _extract_detail(response)
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label=f"Hub {response.status_code}",
            status_tone="danger",
            detail=detail,
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    try:
        payload = response.json()
    except ValueError:
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Invalid hub response",
            status_tone="danger",
            detail="Hub returned a non-JSON payload.",
            detail_tone="danger",
            signed_at=None,
            manifest_digest=None,
            manifest_digest_short=None,
            file_count=None,
            total_bytes=None,
            has_bundle=None,
        )

    metadata = payload.get("metadata") or {}
    signed_at = _normalize_datetime(metadata.get("signed_at"))
    digest = metadata.get("manifest_digest")
    digest_short = _shorten_hex(digest)
    file_count = _safe_int(payload.get("file_count"))
    total_bytes = _safe_int(payload.get("total_bytes"))
    has_bundle = bool(payload.get("has_bundle"))

    if has_bundle:
        return PeerStatus(
            name=peer.name,
            peer_kind="hub",
            peer_kind_label="Hub peer",
            location=location,
            location_label="Hub URL",
            is_hub=True,
            public_key_hint=_format_public_key(peer.public_key),
            status_label="Bundle ready",
            status_tone="success",
            detail=None,
            detail_tone="muted",
            signed_at=signed_at,
            manifest_digest=digest,
            manifest_digest_short=digest_short,
            file_count=file_count,
            total_bytes=total_bytes,
            has_bundle=True,
        )

    return PeerStatus(
        name=peer.name,
        peer_kind="hub",
        peer_kind_label="Hub peer",
        location=location,
        location_label="Hub URL",
        is_hub=True,
        public_key_hint=_format_public_key(peer.public_key),
        status_label="Awaiting bundle",
        status_tone="warning",
        detail="Hub reports no bundle for this peer yet.",
        detail_tone="warning",
        signed_at=signed_at,
        manifest_digest=digest,
        manifest_digest_short=digest_short,
        file_count=file_count,
        total_bytes=total_bytes,
        has_bundle=False,
    )


def _build_hub_status_url(peer: Peer) -> str:
    base = (peer.url or "").rstrip("/")
    return f"{base}/api/v1/sync/{peer.name}/status"


def _perform_hub_request(url: str, *, headers: dict[str, str], timeout: float) -> httpx.Response:
    with httpx.Client(timeout=timeout) as client:
        return client.get(url, headers=headers)


def _extract_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
        detail = data.get("detail")
        if detail:
            return str(detail)
    except Exception:  # noqa: BLE001 - fall back to text response
        pass
    text = response.text.strip()
    return text or "Hub returned an error."


def _format_public_key(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = "".join(value.split())
    if len(cleaned) <= 12:
        return cleaned
    return f"{cleaned[:6]}…{cleaned[-6:]}"


def _shorten_hex(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    if len(trimmed) <= 14:
        return trimmed
    return f"{trimmed[:8]}…{trimmed[-4:]}"


def _normalize_datetime(value: Optional[datetime | str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def _classify_signature_error(message: str) -> tuple[str, str]:
    lowered = message.lower()
    if "missing" in lowered or "not found" in lowered:
        return "Awaiting bundle", "warning"
    return "Signature error", "danger"


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = ["collect_peer_statuses", "PeerStatus"]
