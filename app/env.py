"""Environment loading utilities."""

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def ensure_env_loaded() -> None:
    """Load .env file once if present."""
    load_dotenv()


__all__ = ["ensure_env_loaded"]
