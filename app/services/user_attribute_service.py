from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import UserAttribute

INVITED_BY_USER_ID_KEY = "invited_by_user_id"
INVITE_TOKEN_USED_KEY = "invite_token_used"
PROFILE_PHOTO_URL_KEY = "profile_photo_url"
UI_HIDE_CAPTIONS_KEY = "ui_hide_captions"
UI_CAPTION_DISMISSALS_KEY = "ui_caption_dismissals"
_SIGNAL_DISPLAY_NAME_PREFIX = "signal_display_name:"


def get_attribute(session: Session, *, user_id: int, key: str) -> Optional[str]:
    record = session.exec(
        select(UserAttribute).where(
            UserAttribute.user_id == user_id,
            UserAttribute.key == key,
        )
    ).first()
    return record.value if record else None


def get_attributes(session: Session, *, user_id: int) -> dict[str, Optional[str]]:
    records = session.exec(select(UserAttribute).where(UserAttribute.user_id == user_id)).all()
    return {record.key: record.value for record in records}


def load_profile_photo_urls(session: Session, *, user_ids: list[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    rows = session.exec(
        select(UserAttribute)
        .where(UserAttribute.user_id.in_(user_ids))
        .where(UserAttribute.key == PROFILE_PHOTO_URL_KEY)
    ).all()
    return {row.user_id: row.value for row in rows if row and row.value}


def load_display_names(
    session: Session, *, user_ids: list[int], group_slug: Optional[str] = None
) -> dict[int, str]:
    """Return the best-known display name for each user id."""

    if not user_ids:
        return {}

    statement = select(UserAttribute.user_id, UserAttribute.value).where(
        UserAttribute.user_id.in_(user_ids)
    )
    if group_slug:
        key = f"{_SIGNAL_DISPLAY_NAME_PREFIX}{group_slug}"
        statement = statement.where(UserAttribute.key == key)
    else:
        statement = statement.where(UserAttribute.key.like(f"{_SIGNAL_DISPLAY_NAME_PREFIX}%"))
    statement = statement.order_by(UserAttribute.updated_at.desc(), UserAttribute.id.desc())

    rows = session.exec(statement).all()
    display_names: dict[int, str] = {}
    for user_id, value in rows:
        if not value or user_id is None:
            continue
        if group_slug or user_id not in display_names:
            display_names[user_id] = value
    return display_names


def list_invitee_user_ids(session: Session, *, inviter_user_id: int) -> list[int]:
    """Return user IDs that were invited by the given user."""

    rows = session.exec(
        select(UserAttribute.user_id)
        .where(UserAttribute.key == INVITED_BY_USER_ID_KEY)
        .where(UserAttribute.value == str(inviter_user_id))
    ).all()

    invitee_ids: list[int] = []
    for row in rows:
        value = row[0] if isinstance(row, tuple) else row
        if value is None:
            continue
        try:
            invitee_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return invitee_ids


def set_attribute(
    session: Session,
    *,
    user_id: int,
    key: str,
    value: Optional[str],
    actor_user_id: Optional[int],
) -> UserAttribute:
    now = datetime.utcnow()
    previous_value: Optional[str] = None
    record = session.exec(
        select(UserAttribute).where(
            UserAttribute.user_id == user_id,
            UserAttribute.key == key,
        )
    ).first()

    if record:
        previous_value = record.value
        record.value = value
        record.updated_at = now
        record.updated_by_user_id = actor_user_id
    else:
        record = UserAttribute(
            user_id=user_id,
            key=key,
            value=value,
            created_at=now,
            updated_at=now,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        session.add(record)

    session.flush()

    if key == INVITED_BY_USER_ID_KEY:
        affected_user_ids = {user_id}
        for raw_value in (value, previous_value):
            if not raw_value:
                continue
            try:
                affected_user_ids.add(int(raw_value))
            except (TypeError, ValueError):
                continue
        from app.services import invite_map_cache_service

        invite_map_cache_service.invalidate_many(session, affected_user_ids)

    return record


def delete_attribute(session: Session, *, user_id: int, key: str) -> None:
    record = session.exec(
        select(UserAttribute).where(
            UserAttribute.user_id == user_id,
            UserAttribute.key == key,
        )
    ).first()
    if record:
        session.delete(record)
        session.flush()
