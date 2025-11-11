from __future__ import annotations

from fastapi import FastAPI

from .routes import router


def create_hub_app() -> FastAPI:
    app = FastAPI(title="WhiteBalloon Sync Hub", version="0.1.0")
    app.include_router(router)
    return app


hub_app = create_hub_app()


__all__ = ["create_hub_app", "hub_app"]
