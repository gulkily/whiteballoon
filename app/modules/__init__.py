"""Feature modules for WhiteBalloon."""

from fastapi import FastAPI

from app.modules.requests import router as requests_router
from app.modules.requests import templates as requests_templates


def register_modules(app: FastAPI) -> None:
    app.include_router(requests_router)
    app.include_router(requests_templates.router)


__all__ = ["register_modules"]
