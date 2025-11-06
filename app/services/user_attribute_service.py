from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import UserAttribute

INVITED_BY_USER_ID_KEY = "invited_by_user_id"
INVITE_TOKEN_USED_KEY = "invite_token_used"
PROFILE_PHOTO_URL_KEY = "profile_photo_url"


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


def set_attribute(
    session: Session,
    *,
    user_id: int,
    key: str,
    value: Optional[str],
    actor_user_id: Optional[int],
) -> UserAttribute:
    now = datetime.utcnow()
    record = session.exec(
        select(UserAttribute).where(
            UserAttribute.user_id == user_id,
            UserAttribute.key == key,
        )
    ).first()

    if record:
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
