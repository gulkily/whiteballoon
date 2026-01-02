"""Aggregate router for requests-related submodules."""

from fastapi import APIRouter

from . import recurring

router = APIRouter(tags=["ui"])
router.include_router(recurring.router)

__all__ = ["router"]
