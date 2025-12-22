from __future__ import annotations

from datetime import datetime
import secrets

from sqlmodel import Session, select

from app.models import RssFeedToken

TOKEN_BYTES = 32


def _generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def _get_token_record(session: Session, *, user_id: int, category: str) -> RssFeedToken | None:
    statement = select(RssFeedToken).where(
        RssFeedToken.user_id == user_id,
        RssFeedToken.category == category,
    )
    return session.exec(statement).first()


def list_tokens_for_user(session: Session, *, user_id: int) -> list[RssFeedToken]:
    statement = (
        select(RssFeedToken)
        .where(RssFeedToken.user_id == user_id)
        .order_by(RssFeedToken.category.asc())
    )
    return list(session.exec(statement).all())


def get_or_create_token(session: Session, *, user_id: int, category: str) -> RssFeedToken:
    record = _get_token_record(session, user_id=user_id, category=category)
    if record:
        return record
    token = RssFeedToken(user_id=user_id, category=category, token=_generate_token())
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def rotate_token(session: Session, *, user_id: int, category: str) -> RssFeedToken:
    token = _get_token_record(session, user_id=user_id, category=category)
    if not token:
        return get_or_create_token(session, user_id=user_id, category=category)
    token.token = _generate_token()
    token.rotated_at = datetime.utcnow()
    token.revoked_at = None
    token.last_used_at = None
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def revoke_token(session: Session, *, user_id: int, category: str) -> None:
    token = _get_token_record(session, user_id=user_id, category=category)
    if not token:
        return
    token.revoked_at = datetime.utcnow()
    session.add(token)
    session.commit()


def get_token_by_secret(session: Session, *, token_value: str) -> RssFeedToken | None:
    if not token_value:
        return None
    statement = select(RssFeedToken).where(RssFeedToken.token == token_value)
    record = session.exec(statement).first()
    if not record or record.revoked_at:
        return None
    return record


def record_access(session: Session, *, token: RssFeedToken) -> None:
    token.last_used_at = datetime.utcnow()
    session.add(token)
    session.commit()
