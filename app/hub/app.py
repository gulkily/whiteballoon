from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .routes import router


def create_hub_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon Sync Hub", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return """
        <html>
          <head><title>WhiteBalloon Sync Hub</title></head>
          <body style="font-family: sans-serif; padding: 2rem;">
            <h1>WhiteBalloon Sync Hub</h1>
            <p>This service accepts signed sync bundles via <code>POST /api/v1/sync/&lt;peer&gt;/bundle</code>
               and serves the latest bundle at <code>GET /api/v1/sync/&lt;peer&gt;/bundle</code>.</p>
            <p>Configure peers in <code>WB_HUB_CONFIG</code> and use <code>./wb sync push &lt;peer&gt;</code> / <code>./wb sync pull &lt;peer&gt;</code>
               to interact with the hub.</p>
          </body>
        </html>
        """

    app.include_router(router)
    return app


hub_app = create_hub_app()


__all__ = ["create_hub_app", "hub_app"]
