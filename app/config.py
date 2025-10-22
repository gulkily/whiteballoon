from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "on", "yes"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    secret_key: str = os.getenv("SECRET_KEY", "changeme")
    session_expiry_minutes: int = int(os.getenv("SESSION_EXPIRY_MINUTES", "20160"))
    cookie_secure: bool = _get_bool(os.getenv("COOKIE_SECURE"), False)
    enable_contact_email: bool = _get_bool(os.getenv("ENABLE_CONTACT_EMAIL"), True)


@lru_cache(maxsize=1)
def _build_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    return _build_settings()


def reset_settings_cache() -> None:
    _build_settings.cache_clear()
