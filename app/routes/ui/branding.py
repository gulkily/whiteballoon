from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.routes.ui.helpers import templates

router = APIRouter(tags=["ui"])


@router.get("/brand/logo", include_in_schema=False)
def logo_capture(request: Request) -> Response:
    """Render a padded, standalone logo for easy screenshots."""
    return templates.TemplateResponse("branding/logo_capture.html", {"request": request})


@router.get("/brand/logo/flat", include_in_schema=False)
def logo_capture_flat(request: Request) -> Response:
    """Render a flat, rectangular logo layout for screenshots."""
    return templates.TemplateResponse("branding/logo_capture_flat.html", {"request": request})
