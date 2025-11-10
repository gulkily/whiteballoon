from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import User
from app.services import vouch_service


def test_create_vouch() -> None:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        voucher = User(username="voucher")
        subject = User(username="subject")
        session.add(voucher)
        session.add(subject)
        session.commit()
        session.refresh(voucher)
        session.refresh(subject)

        vouch = vouch_service.create_vouch(session, voucher.id, subject.id, signature="sig")
        assert vouch.voucher_user_id == voucher.id
        assert vouch.subject_user_id == subject.id
        assert vouch.signature == "sig"

        again = vouch_service.create_vouch(session, voucher.id, subject.id)
        assert again.id == vouch.id
