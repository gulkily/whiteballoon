"""Helpers to redact sensitive tokens before logging."""
from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Iterable

MAX_TEXT_LENGTH = 6000
_SENSITIVE_ENV_KEYS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS", "PWD", "BEARER")
_GENERIC_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{16,}", re.IGNORECASE),
    re.compile(r"token=([A-Za-z0-9_-]{8,})", re.IGNORECASE),
)


def _iter_sensitive_literals() -> Iterable[str]:
    for key, value in os.environ.items():
        if not value:
            continue
        upper_key = key.upper()
        if any(fragment in upper_key for fragment in _SENSITIVE_ENV_KEYS):
            yield value


@lru_cache(maxsize=1)
def _sensitive_literals() -> tuple[str, ...]:
    values = sorted(set(_iter_sensitive_literals()), key=len, reverse=True)
    return tuple(values)


def _apply_literal_masks(text: str) -> str:
    masked = text
    for literal in _sensitive_literals():
        if literal and literal in masked:
            masked = masked.replace(literal, "[redacted]")
    return masked


def _apply_pattern_masks(text: str) -> str:
    masked = text
    for pattern in _GENERIC_PATTERNS:
        masked = pattern.sub("[redacted]", masked)
    return masked


def redact_text(value: str | None) -> str | None:
    """Return text with obvious secrets removed and length bounded."""

    if not value:
        return value
    masked = _apply_literal_masks(value)
    masked = _apply_pattern_masks(masked)
    if len(masked) <= MAX_TEXT_LENGTH:
        return masked
    return masked[:MAX_TEXT_LENGTH] + " …[truncated]"
