from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import HelpRequest, RequestComment, User
from app.sync.export_import import export_sync_data, import_sync_data


def test_export_import_round_trip(tmp_path: Path) -> None:
    source_engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(source_engine)
    with Session(source_engine) as session:
        user = User(username="founder", sync_scope="public")
        session.add(user)
        session.commit()
        session.refresh(user)

        request = HelpRequest(description="Public help", created_by_user_id=user.id, sync_scope="public")
        session.add(request)
        session.commit()
        session.refresh(request)

        comment = RequestComment(
            help_request_id=request.id,
            user_id=user.id,
            body="cheering",
            sync_scope="public",
        )
        session.add(comment)
        session.commit()

        files = export_sync_data(session, tmp_path)
        assert any(path.name.startswith("user_") for path in files)
        assert any(path.name.startswith("request_") for path in files)

    target_engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(target_engine)
    with Session(target_engine) as session:
        imported = import_sync_data(session, tmp_path)
        assert imported >= 2

        users = session.query(User).all()
        assert len(users) == 1
        assert users[0].username == "founder"

        requests = session.query(HelpRequest).all()
        assert len(requests) == 1
        assert requests[0].description == "Public help"

        comments = session.query(RequestComment).all()
        assert len(comments) == 1
        assert comments[0].body == "cheering"
