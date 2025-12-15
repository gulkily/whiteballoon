from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Tuple

from app.env import ensure_env_loaded

ensure_env_loaded()


def _get_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "on", "yes"}


def _parse_csv(value: str | None) -> Tuple[str, ...]:
    if not value:
        return tuple()
    parts = []
    for chunk in value.split(","):
        item = chunk.strip()
        if item:
            parts.append(item)
    return tuple(parts)


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    secret_key: str = os.getenv("SECRET_KEY", "changeme")
    session_expiry_minutes: int = int(os.getenv("SESSION_EXPIRY_MINUTES", "20160"))
    cookie_secure: bool = _get_bool(os.getenv("COOKIE_SECURE"), False)
    enable_contact_email: bool = _get_bool(os.getenv("ENABLE_CONTACT_EMAIL"), True)
    site_url: str = os.getenv("SITE_URL", "http://127.0.0.1:8000")
    skins_enabled: bool = _get_bool(os.getenv("WB_SKINS_ENABLED"), False)
    skin_default: str = os.getenv("WB_SKIN_DEFAULT", "default")
    skins_allowed: tuple[str, ...] = _parse_csv(os.getenv("WB_SKINS_ALLOWED", ""))
    skins_manifest_path: str = os.getenv("WB_SKINS_MANIFEST_PATH", "static/build/skins/manifest.json")
    skin_preview_enabled: bool = _get_bool(os.getenv("WB_SKIN_PREVIEW_ENABLED"), False)
    skin_preview_param: str = os.getenv("WB_SKIN_PREVIEW_PARAM", "skin")
    skin_strict: bool = _get_bool(os.getenv("WB_SKIN_STRICT"), False)
    dedalus_api_key: str = os.getenv("DEDALUS_API_KEY", "")
    dedalus_api_key_verified_at: Optional[str] = os.getenv("DEDALUS_API_KEY_VERIFIED_AT")
    dedalus_log_retention_days: int = int(os.getenv("DEDALUS_LOG_RETENTION_DAYS", "30"))
    comment_insights_indicator_enabled: bool = _get_bool(os.getenv("COMMENT_INSIGHTS_INDICATOR"), False)
    profile_signal_glaze_enabled: bool = _get_bool(os.getenv("PROFILE_SIGNAL_GLAZE"), False)
    pinned_requests_limit: int = int(os.getenv("WB_PINNED_REQUESTS_LIMIT", "3"))
    request_channels_enabled: bool = _get_bool(os.getenv("REQUEST_CHANNELS"), False)
    recurring_template_poll_seconds: int = int(os.getenv("RECURRING_TEMPLATE_POLL_SECONDS", "300"))


@lru_cache(maxsize=1)
def _build_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    return _build_settings()


def reset_settings_cache() -> None:
    _build_settings.cache_clear()
