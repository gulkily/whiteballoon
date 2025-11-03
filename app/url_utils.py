from __future__ import annotations

from typing import Optional

from fastapi import Request

from app.config import get_settings


def get_base_url(request: Optional[Request] = None) -> str:
    if request is not None:
        base = str(request.base_url).rstrip('/')
        if base:
            return base
    settings = get_settings()
    return settings.site_url.rstrip('/')


def build_invite_link(token: str, request: Optional[Request] = None) -> str:
    base = get_base_url(request)
    return f"{base}/register?invite_token={token}"
