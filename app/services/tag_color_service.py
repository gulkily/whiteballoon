from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List


@dataclass(frozen=True)
class TagHue:
    """Represents a tag label paired with its deterministic hue."""

    label: str
    slug: str
    hue: int | None

    def to_dict(self) -> dict[str, object]:
        return {"label": self.label, "slug": self.slug, "hue": self.hue}


def _normalize(label: str | None) -> str | None:
    if not label:
        return None
    cleaned = label.strip().lower()
    return cleaned or None


@lru_cache(maxsize=512)
def hue_for_slug(slug: str) -> int:
    """Return deterministic hue 0-359 for a slug."""

    digest = hashlib.md5(slug.encode("utf-8")).hexdigest()
    value = int(digest, 16)
    return value % 360


def build_tag_hues(labels: Iterable[str]) -> List[TagHue]:
    entries: list[TagHue] = []
    for label in labels:
        slug = _normalize(label)
        if not slug:
            continue
        hue = hue_for_slug(slug)
        entries.append(TagHue(label=label, slug=slug, hue=hue))
    return entries


def serialize_tag_hues(labels: Iterable[str]) -> list[dict[str, object]]:
    return [entry.to_dict() for entry in build_tag_hues(labels)]

