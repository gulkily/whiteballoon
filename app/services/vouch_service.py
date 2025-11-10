from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlmodel import Session, select

from app.models import User, Vouch


def list_unvouched_roots(session: Session) -> list[User]:
    roots = session.exec(
        select(User).where(~select(User.id).where(User.id == User.id)).limit(0)
    )
    # Placeholder; actual root detection will come later.
    return session.exec(select(User)).all()


def create_vouch(session: Session, voucher_id: int, subject_id: int, signature: str | None = None) -> Vouch:
    existing = session.exec(
        select(Vouch).where(
            Vouch.voucher_user_id == voucher_id,
            Vouch.subject_user_id == subject_id,
        )
    ).first()
    if existing:
        return existing
    vouch = Vouch(
        voucher_user_id=voucher_id,
        subject_user_id=subject_id,
        signature=signature,
        created_at=datetime.utcnow(),
    )
    session.add(vouch)
    session.commit()
    session.refresh(vouch)
    return vouch


def list_vouches(session: Session) -> list[Vouch]:
    return session.exec(select(Vouch)).all()
