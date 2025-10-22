"""Feature modules for WhiteBalloon."""

from fastapi import FastAPI

from app.modules.requests import router as requests_router


def register_modules(app: FastAPI) -> None:
    app.include_router(requests_router)


__all__ = ["register_modules"]
