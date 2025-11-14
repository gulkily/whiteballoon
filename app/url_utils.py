from __future__ import annotations

import base64
import io
from typing import Optional

from fastapi import Request
import qrcode

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
    return f"{base}/register/{token}"


def generate_qr_code_data_url(text: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"
