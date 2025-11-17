from __future__ import annotations

import io
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from app.sync.signing import (
    MANIFEST_FILENAME,
    SIGNATURE_FILENAME,
    SignatureMetadata,
    SignatureVerificationError,
    verify_bundle_signature,
)

from .config import HubPeer, HubSettings, get_settings, hash_token, persist_peer, reset_settings_cache
from .feed import ingest_bundle
from .pending import queue_pending_key
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
logger = logging.getLogger("whiteballoon.hub")
PUBLIC_KEY_HEADER = "x-wb-public-key"


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return token


def _require_public_key(request: Request) -> str:
    public_key = request.headers.get(PUBLIC_KEY_HEADER)
    if not public_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-WB-Public-Key header")
    return public_key.strip()


def _extract_bundle(upload: UploadFile, tmp_dir: Path) -> tuple[Path, Path]:
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
    return manifest.parent, bundle_path


def _verify_bundle(bundle_root: Path) -> SignatureMetadata:
    try:
        return verify_bundle_signature(bundle_root, expected_public_key=None)
    except SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{peer_name}/bundle", status_code=status.HTTP_202_ACCEPTED)
async def upload_bundle(
    peer_name: str,
    request: Request,
    bundle: UploadFile = File(..., description="Tar.gz of data/public_sync"),
    settings: HubSettings = Depends(get_settings),
) -> dict[str, object]:
    peer = settings.get_peer(peer_name)
    auto_registered = False
    if not peer:
        if not settings.allow_auto_register_push:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown peer")
        token = _extract_bearer_token(request)
        public_key = _require_public_key(request)
        peer = HubPeer(name=peer_name, token_hash=hash_token(token), public_keys=(public_key,))
        auto_registered = True
    else:
        auth = AuthContext(request, settings)
        auth.authenticate(peer_name=peer_name)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bundle_root, bundle_archive = _extract_bundle(bundle, tmp_path)
        signature_meta = _verify_bundle(bundle_root)
        if not peer.allows_public_key(signature_meta.public_key_b64):
            pending = queue_pending_key(
                peer_name=peer.name,
                presented_key=signature_meta.public_key_b64,
                bundle_source=bundle_archive,
                manifest_digest=signature_meta.manifest_digest,
                signed_at=signature_meta.signed_at,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "peer_key_mismatch",
                    "message": "Signature public key does not match stored keys; approval required",
                    "peer": peer.name,
                    "pending_id": pending.id,
                },
            )
        digest = signature_meta.manifest_digest
        signed_at = signature_meta.signed_at
        metadata = build_metadata(peer, digest, signed_at)
        write_bundle(settings, peer, bundle_root, metadata)
        summary = summarize_bundle(bundle_root)
        stored_bundle = get_bundle_path(settings, peer)
        try:
            ingest_bundle(
                stored_bundle,
                peer_name=peer.name,
                manifest_digest=digest,
                signed_at=signed_at,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Feed ingest failed for peer '%s'", peer.name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bundle stored but feed ingest failed",
            ) from exc
    if auto_registered:
        if not settings.config_path:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Hub config path unavailable")
        persist_peer(settings.config_path, peer, storage_dir=settings.storage_dir, allow_push=settings.allow_auto_register_push, allow_pull=settings.allow_auto_register_pull)
        reset_settings_cache()
        logger.info("Auto-registered peer '%s' via push", peer_name)
    return {
        "peer": peer.name,
        "manifest_digest": digest,
        "signed_at": signed_at.isoformat(),
        "stored_bytes": summary["total_bytes"],
        "stored_files": summary["file_count"],
        "auto_registered": auto_registered,
    }


@router.get("/{peer_name}/bundle")
async def download_bundle(
    peer_name: str,
    request: Request,
    settings: HubSettings = Depends(get_settings),
) -> Response:
    peer = settings.get_peer(peer_name)
    auto_registered = False
    if not peer:
        if not settings.allow_auto_register_pull:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown peer")
        token = _extract_bearer_token(request)
        public_key = _require_public_key(request)
        peer = HubPeer(name=peer_name, token_hash=hash_token(token), public_keys=(public_key,))
        auto_registered = True
        if not settings.config_path:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Hub config path unavailable")
        persist_peer(settings.config_path, peer, storage_dir=settings.storage_dir, allow_push=settings.allow_auto_register_push, allow_pull=settings.allow_auto_register_pull)
        reset_settings_cache()
        logger.info("Auto-registered peer '%s' via pull", peer_name)
    else:
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
    response = StreamingResponse(
        buffer,
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
    response.headers["X-WB-Auto-Registered"] = "true" if auto_registered else "false"
    return response


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
