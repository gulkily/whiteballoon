from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session

from app.services import caption_preference_service


@dataclass(slots=True)
class CaptionPreferences:
    user_id: Optional[int]
    hide_all: bool
    dismissed_ids: set[str]

    def should_show(self, caption_id: str) -> bool:
        if self.hide_all:
            return False
        return caption_id not in self.dismissed_ids


def load_preferences(session: Session, user_id: Optional[int]) -> CaptionPreferences:
    if not user_id:
        return CaptionPreferences(user_id=None, hide_all=False, dismissed_ids=set())
    return CaptionPreferences(
        user_id=user_id,
        hide_all=caption_preference_service.get_global_hidden(session, user_id),
        dismissed_ids=caption_preference_service.get_dismissed_captions(session, user_id),
    )


def build_caption_payload(
    preferences: CaptionPreferences,
    *,
    caption_id: str,
    text: str,
    tone: str = "info",
) -> dict[str, object]:
    return {
        "id": caption_id,
        "text": text,
        "tone": tone,
        "show": preferences.should_show(caption_id),
    }


__all__ = ["CaptionPreferences", "load_preferences", "build_caption_payload"]
