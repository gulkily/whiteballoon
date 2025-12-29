from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

_PATTERN = re.compile(r"\s*\(Reactions:\s*(?P<entries>.+?)\)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class ChatReaction:
    emoji: str
    count: int


def strip_reactions(text: str) -> tuple[str, list[ChatReaction]]:
    if not text:
        return text, []
    match = _PATTERN.search(text)
    if not match:
        return text, []

    entries_segment = match.group("entries") or ""
    cleaned_body = text[: match.start()].rstrip()
    counts = defaultdict(int)

    for raw_entry in entries_segment.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        _, _, emoji = entry.rpartition(" ")
        emoji = emoji.strip()
        if not emoji:
            continue
        counts[emoji] += 1

    if not counts:
        return cleaned_body, []

    summary = sorted(
        (ChatReaction(emoji=emoji, count=count) for emoji, count in counts.items()),
        key=lambda reaction: (-reaction.count, reaction.emoji),
    )
    return cleaned_body, summary


__all__ = ["ChatReaction", "strip_reactions"]
