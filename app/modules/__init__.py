"""Feature modules for WhiteBalloon."""

from fastapi import FastAPI

from app.modules.requests import router as requests_router
from app.modules.messaging.routes import router as messaging_router


def register_modules(app: FastAPI) -> None:
    app.include_router(requests_router)
    app.include_router(messaging_router)


__all__ = ["register_modules"]
