from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.hub.config import get_settings
from app.hub.storage import summarize_bundle, METADATA_FILENAME
from app.sync.signing import ensure_local_keypair

from .admin import admin_router
from .routes import router


def create_hub_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon Sync Hub", version="0.1.0")
    logger = logging.getLogger("whiteballoon.hub")

    @app.on_event("startup")
    async def _log_settings() -> None:
        settings = get_settings()
        logger.info(
            "Hub config: %s | auto-register push=%s pull=%s",
            settings.config_path,
            settings.allow_auto_register_push,
            settings.allow_auto_register_pull,
        )

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        settings = get_settings()
        peer_stats = []
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
                    peer_stats.append((peer_dir.name, summary["file_count"], summary["total_bytes"], signed_at, digest))
        try:
            key, _ = ensure_local_keypair(auto_generate=True)
            public_key = key.public_key_b64 if key else "Not generated yet"
        except Exception:
            public_key = "Unavailable"
        stats_rows = "".join(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{files}</td>"
            f"<td>{bytes // 1024} KB</td>"
            f"<td>{signed}</td>"
            f"<td><code>{digest}</code></td>"
            f"</tr>"
            for name, files, bytes, signed, digest in peer_stats
        ) or "<tr><td colspan='5'>No bundles stored yet.</td></tr>"
        return f"""
        <!DOCTYPE html>
        <html lang=\"en\">
          <head>
            <meta charset=\"utf-8\" />
            <title>WhiteBalloon Sync Hub</title>
            <style>
              :root {{
                color-scheme: light dark;
                --bg-primary: linear-gradient(135deg, #1b62f2 0%, #7b5df5 50%, #fb88ff 100%);
                --panel-bg: rgba(255, 255, 255, 0.9);
                --text-color: #1f1f29;
              }}
              body {{
                margin: 0;
                min-height: 100vh;
                font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: var(--bg-primary);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                color: var(--text-color);
              }}
              .panel {{
                background: var(--panel-bg);
                box-shadow: 0 25px 60px rgba(23, 23, 45, 0.25);
                border-radius: 32px;
                padding: 2.5rem;
                max-width: 900px;
                width: 100%;
                backdrop-filter: blur(12px);
              }}
              h1 {{
                margin-top: 0;
                font-size: 2.5rem;
                color: #211547;
              }}
              p {{
                line-height: 1.6;
                font-size: 1.05rem;
              }}
              code {{
                background: rgba(33, 21, 71, 0.08);
                padding: 0.15rem 0.35rem;
                border-radius: 6px;
                font-size: 0.95rem;
              }}
              ul {{
                padding-left: 1.25rem;
              }}
              .tag {{
                display: inline-block;
                margin-right: 0.5rem;
                padding: 0.2rem 0.6rem;
                border-radius: 999px;
                background: rgba(29, 110, 253, 0.15);
                color: #1d6efd;
                font-size: 0.85rem;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                font-weight: 600;
              }}
              table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 1.5rem;
              }}
              th, td {{
                text-align: left;
                padding: 0.6rem 0.75rem;
              }}
              th {{
                font-size: 0.85rem;
                color: #5c5a6d;
                letter-spacing: 0.04em;
                text-transform: uppercase;
              }}
              tr:nth-child(even) {{
                background: rgba(33, 21, 71, 0.05);
              }}
            </style>
          </head>
          <body>
            <main class=\"panel\">
              <span class=\"tag\">WhiteBalloon</span>
              <h1>Sync Hub Relay</h1>
              <p>
                <span class=\"tag\">Loose push: {'ON' if settings.allow_auto_register_push else 'OFF'}</span>
                <span class=\"tag\">Loose pull: {'ON' if settings.allow_auto_register_pull else 'OFF'}</span>
              </p>
              <p>
                Welcome to the bridge between WhiteBalloon communities. This hub ferries the public heartbeat
                of each node—requests, invites, vouches—so distant clusters can stay in tune with one another.
              </p>
              <p>
                Hub public key:<br />
                <code>{public_key}</code>
              </p>
              <p>
                Operators can push fresh stories from their local node and pull the latest from peers, weaving
                trust across time zones. Every bundle is signed, so authenticity flows right alongside warmth.
              </p>
              <p>
                Ready to explore?
              </p>
              <ul>
                <li>Share your universe: <code>./wb sync push &lt;peer&gt;</code></li>
                <li>Collect new constellations: <code>./wb sync pull &lt;peer&gt;</code></li>
              </ul>
              <div class=\"stats\">
                <p><strong>Stored bundles:</strong></p>
                <p>Total peers: {len(peer_stats)} · Files: {total_files} · Size: {total_bytes // 1024} KB</p>
                <table>
                  <thead>
                    <tr>
                      <th>Peer</th>
                      <th>Files</th>
                      <th>Size</th>
                      <th>Last Signed</th>
                      <th>Digest</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats_rows}
                  </tbody>
                </table>
              </div>
              <p>
                Configure peers + tokens in <code>WB_HUB_CONFIG</code>, then let the CLI handle the journey.
                This page is just a postcard; the real magic happens between communities.
              </p>
            </main>
          </body>
        </html>
        """

    app.include_router(admin_router)
    app.include_router(router)
    return app


hub_app = create_hub_app()


__all__ = ["create_hub_app", "hub_app"]
