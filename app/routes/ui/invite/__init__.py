"""UI route handlers for the invite surface.

Routes are extracted from app.routes.ui.__init__ and registered on the main
FastAPI router once this package exposes a configured `router` object.
"""

from fastapi import APIRouter

router = APIRouter(tags=["ui"])
