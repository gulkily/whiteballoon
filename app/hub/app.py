from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings as get_core_settings
from app.hub.config import get_settings
from app.hub.feed import DEFAULT_FEED_PAGE_SIZE, feed_api_router, list_feed_requests
from app.hub.storage import summarize_bundle, METADATA_FILENAME
from app.sync.signing import ensure_local_keypair
from app.skins.runtime import register_skin_helpers

from .admin import admin_router
from .routes import router

templates = Jinja2Templates(directory="templates")
register_skin_helpers(templates)
templates.env.globals.setdefault("site_title", lambda: get_core_settings().site_title)


def create_hub_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon Sync Hub", version="0.1.0")
    logger = logging.getLogger("whiteballoon.hub")

    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    async def _log_settings() -> None:
        settings = get_settings()
        logger.info(
            "Hub config: %s | auto-register push=%s pull=%s",
            settings.config_path,
            settings.allow_auto_register_push,
            settings.allow_auto_register_pull,
        )

    @app.get("/")
    def home(request: Request):
        settings = get_settings()
        peer_stats: list[dict[str, object]] = []
        total_files = 0
        total_bytes = 0
        if settings.storage_dir.exists():
            for peer_dir in settings.storage_dir.iterdir():
                if peer_dir.is_dir():
                    summary = summarize_bundle(peer_dir)
                    total_files += summary["file_count"]
                    total_bytes += summary["total_bytes"]
                    signed_at = "—"
                    digest = "—"
                    meta_path = peer_dir / METADATA_FILENAME
                    if meta_path.exists():
                        try:
                            meta = json.loads(meta_path.read_text(encoding="utf-8"))
                            signed_at = meta.get("signed_at", "—")
                            digest = meta.get("manifest_digest", "—")
                        except Exception:
                            pass
                    peer_stats.append(
                        {
                            "name": peer_dir.name,
                            "file_count": summary["file_count"],
                            "total_bytes": summary["total_bytes"],
                            "signed_at": signed_at,
                            "digest": digest,
                            "has_bundle": summary["file_count"] > 0,
                        }
                    )
        try:
            key, _ = ensure_local_keypair(auto_generate=True)
            public_key = key.public_key_b64 if key else "Not generated yet"
        except Exception:
            public_key = "Unavailable"

        truncated_key = (
            public_key[:80] + "…" if isinstance(public_key, str) and len(public_key) > 80 else public_key
        )
        ready_count = sum(1 for entry in peer_stats if entry["has_bundle"])

        feed_page = list_feed_requests(limit=DEFAULT_FEED_PAGE_SIZE, offset=0)
        context = {
            "request": request,
            "peer_stats": peer_stats,
            "total_files": total_files,
            "total_bytes": total_bytes,
            "total_kilobytes": total_bytes // 1024,
            "public_key": public_key,
            "truncated_key": truncated_key,
            "ready_count": ready_count,
            "has_peers": bool(peer_stats),
            "feed_page": feed_page,
            "feed_page_size": DEFAULT_FEED_PAGE_SIZE,
            "has_feed": bool(feed_page.items),
        }
        return templates.TemplateResponse("hub/home.html", context)


    app.include_router(admin_router)
    app.include_router(router)
    app.include_router(feed_api_router)
    return app


hub_app = create_hub_app()


__all__ = ["create_hub_app", "hub_app"]
