from __future__ import annotations

import json
from typing import Optional

from sqlmodel import Session

from app.services import user_attribute_service


def get_global_hidden(session: Session, user_id: int) -> bool:
    value = user_attribute_service.get_attribute(
        session,
        user_id=user_id,
        key=user_attribute_service.UI_HIDE_CAPTIONS_KEY,
    )
    return value == "1"


def set_global_hidden(session: Session, *, user_id: int, hidden: bool, actor_user_id: Optional[int]) -> None:
    user_attribute_service.set_attribute(
        session,
        user_id=user_id,
        key=user_attribute_service.UI_HIDE_CAPTIONS_KEY,
        value="1" if hidden else None,
        actor_user_id=actor_user_id,
    )


def get_dismissed_captions(session: Session, user_id: int) -> set[str]:
    value = user_attribute_service.get_attribute(
        session,
        user_id=user_id,
        key=user_attribute_service.UI_CAPTION_DISMISSALS_KEY,
    )
    if not value:
        return set()
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return set()
    if isinstance(payload, list):
        return {str(item) for item in payload}
    return set()


def dismiss_caption(
    session: Session,
    *,
    user_id: int,
    caption_id: str,
    actor_user_id: Optional[int],
) -> None:
    dismissals = get_dismissed_captions(session, user_id)
    dismissals.add(caption_id)
    _write_dismissals(session, user_id=user_id, dismissals=dismissals, actor_user_id=actor_user_id)


def reset_dismissals(session: Session, *, user_id: int, actor_user_id: Optional[int]) -> None:
    user_attribute_service.delete_attribute(
        session,
        user_id=user_id,
        key=user_attribute_service.UI_CAPTION_DISMISSALS_KEY,
    )


def _write_dismissals(
    session: Session,
    *,
    user_id: int,
    dismissals: set[str],
    actor_user_id: Optional[int],
) -> None:
    payload = json.dumps(sorted(dismissals))
    user_attribute_service.set_attribute(
        session,
        user_id=user_id,
        key=user_attribute_service.UI_CAPTION_DISMISSALS_KEY,
        value=payload,
        actor_user_id=actor_user_id,
    )
