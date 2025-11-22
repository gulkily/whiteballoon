from __future__ import annotations

import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine

from .models import hub_feed_metadata

DEFAULT_FEED_DB_PATH = Path(os.environ.get("WB_HUB_FEED_DB", "data/hub_feed.db"))


def _database_url() -> str:
    path = DEFAULT_FEED_DB_PATH
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


@lru_cache(maxsize=1)
def get_feed_engine() -> Engine:
    url = _database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def init_feed_db() -> None:
    engine = get_feed_engine()
    hub_feed_metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    engine = get_feed_engine()
    with Session(engine) as session:
        yield session
        session.commit()
