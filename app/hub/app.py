from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .routes import router


def create_hub_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon Sync Hub", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return """
        <!DOCTYPE html>
        <html lang=\"en\">
          <head>
            <meta charset=\"utf-8\" />
            <title>WhiteBalloon Sync Hub</title>
            <style>
              :root {
                color-scheme: light dark;
                --bg-primary: linear-gradient(135deg, #1b62f2 0%, #7b5df5 50%, #fb88ff 100%);
                --panel-bg: rgba(255, 255, 255, 0.9);
                --text-color: #1f1f29;
              }
              body {
                margin: 0;
                min-height: 100vh;
                font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: var(--bg-primary);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                color: var(--text-color);
              }
              .panel {
                background: var(--panel-bg);
                box-shadow: 0 25px 60px rgba(23, 23, 45, 0.25);
                border-radius: 32px;
                padding: 2.5rem;
                max-width: 720px;
                width: 100%;
                backdrop-filter: blur(12px);
              }
              h1 {
                margin-top: 0;
                font-size: 2.5rem;
                color: #211547;
              }
              p {
                line-height: 1.6;
                font-size: 1.05rem;
              }
              code {
                background: rgba(33, 21, 71, 0.08);
                padding: 0.15rem 0.35rem;
                border-radius: 6px;
                font-size: 0.95rem;
              }
              ul {
                padding-left: 1.25rem;
              }
              .tag {
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
              }
            </style>
          </head>
          <body>
            <main class=\"panel\">
              <span class=\"tag\">WhiteBalloon</span>
              <h1>Sync Hub Relay</h1>
              <p>
                This service relays signed <code>data/public_sync</code> bundles between peer instances.
                Use the CLI to manage transfers:
              </p>
              <ul>
                <li><code>./wb sync push &lt;peer&gt;</code> → uploads via <code>POST /api/v1/sync/&lt;peer&gt;/bundle</code></li>
                <li><code>./wb sync pull &lt;peer&gt;</code> → downloads from <code>GET /api/v1/sync/&lt;peer&gt;/bundle</code></li>
              </ul>
              <p>
                Peers and tokens are defined in your <code>WB_HUB_CONFIG</code>. All bundles must include
                <code>bundle.sig</code> and pass the Ed25519 verification performed by the hub.
              </p>
            </main>
          </body>
        </html>
        """

    app.include_router(router)
    return app


hub_app = create_hub_app()


__all__ = ["create_hub_app", "hub_app"]
