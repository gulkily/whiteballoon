from __future__ import annotations

import hashlib
import hmac

from app.config import get_settings


def _secret_bytes() -> bytes:
    return get_settings().secret_key.encode("utf-8")


def generate_csrf_token(session_id: str) -> str:
    secret = _secret_bytes()
    return hmac.new(secret, session_id.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_csrf_token(session_id: str, token: str) -> bool:
    if not session_id or not token:
        return False
    expected = generate_csrf_token(session_id)
    try:
        return hmac.compare_digest(expected, token)
    except ValueError:
        return False


__all__ = ["generate_csrf_token", "validate_csrf_token"]
