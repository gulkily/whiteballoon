from __future__ import annotations

import io
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from app.sync.signing import (
    MANIFEST_FILENAME,
    SIGNATURE_FILENAME,
    SignatureVerificationError,
    verify_bundle_signature,
)

from .config import HubPeer, HubSettings, get_settings
from .security import AuthContext
from .storage import (
    build_metadata,
    bundle_exists,
    get_bundle_path,
    read_metadata,
    summarize_bundle,
    write_bundle,
)

router = APIRouter(prefix="/api/v1/sync", tags=["hub"])


def _extract_bundle(upload: UploadFile, tmp_dir: Path) -> Path:
    bundle_path = tmp_dir / "bundle.tar.gz"
    with bundle_path.open("wb") as fh:
        for chunk in iter(lambda: upload.file.read(1024 * 1024), b""):
            if not chunk:
                break
            fh.write(chunk)
    try:
        with tarfile.open(bundle_path, "r:gz") as tar:
            extraction_root = tmp_dir / "extracted"
            extraction_root.mkdir(parents=True, exist_ok=True)
            for member in tar.getmembers():
                member_path = Path(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Archive contains unsafe paths",
                    )
            tar.extractall(path=extraction_root)
    except tarfile.TarError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid bundle archive") from exc

    manifest = next(extraction_root.rglob(MANIFEST_FILENAME), None)
    if not manifest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manifest missing from bundle")
    return manifest.parent


def _verify_bundle(bundle_root: Path, peer: HubPeer) -> tuple[str, datetime]:
    try:
        metadata = verify_bundle_signature(bundle_root, expected_public_key=peer.public_key)
    except SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return metadata.manifest_digest, metadata.signed_at


@router.post("/{peer_name}/bundle", status_code=status.HTTP_202_ACCEPTED)
async def upload_bundle(
    peer_name: str,
    request: Request,
    bundle: UploadFile = File(..., description="Tar.gz of data/public_sync"),
    settings: HubSettings = Depends(get_settings),
) -> dict[str, object]:
    peer = settings.get_peer(peer_name)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown peer")
    auth = AuthContext(request, settings)
    auth.authenticate(peer_name=peer_name)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bundle_root = _extract_bundle(bundle, tmp_path)
        digest, signed_at = _verify_bundle(bundle_root, peer)
        metadata = build_metadata(peer, digest, signed_at)
        write_bundle(settings, peer, bundle_root, metadata)
        summary = summarize_bundle(bundle_root)
    return {
        "peer": peer.name,
        "manifest_digest": digest,
        "signed_at": signed_at.isoformat(),
        "stored_bytes": summary["total_bytes"],
        "stored_files": summary["file_count"],
    }


@router.get("/{peer_name}/bundle")
async def download_bundle(
    peer_name: str,
    request: Request,
    settings: HubSettings = Depends(get_settings),
) -> Response:
    peer = settings.get_peer(peer_name)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown peer")
    AuthContext(request, settings).authenticate(peer_name=peer_name)

    bundle_root = get_bundle_path(settings, peer)
    manifest_path = bundle_root / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bundle available")

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for file_path in bundle_root.rglob("*"):
            tar.add(file_path, arcname=file_path.relative_to(bundle_root))
    buffer.seek(0)
    filename = f"{peer.name}_public_sync.tar.gz"
    return StreamingResponse(
        buffer,
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{peer_name}/status")
async def bundle_status(
    peer_name: str,
    request: Request,
    settings: HubSettings = Depends(get_settings),
) -> dict[str, object]:
    peer = settings.get_peer(peer_name)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown peer")
    AuthContext(request, settings).authenticate(peer_name=peer_name)

    bundle_root = get_bundle_path(settings, peer)
    exists = bundle_exists(settings, peer)
    metadata = read_metadata(settings, peer)
    summary = summarize_bundle(bundle_root) if exists else {"file_count": 0, "total_bytes": 0}
    return {
        "peer": peer.name,
        "has_bundle": exists,
        "metadata": metadata,
        "file_count": summary["file_count"],
        "total_bytes": summary["total_bytes"],
    }
