from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, create_engine

from app.config import get_settings
from app.modules.messaging.models import messaging_metadata


@lru_cache(maxsize=1)
def get_messaging_engine() -> Engine:
    settings = get_settings()
    database_url = settings.messaging_database_url
    connect_args: dict[str, object] = {}

    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        Path(url.database or "data/messages.db").parent.mkdir(parents=True, exist_ok=True)

    return create_engine(database_url, echo=False, connect_args=connect_args)


def reset_messaging_engine() -> None:
    get_messaging_engine.cache_clear()


def init_messaging_db() -> None:
    engine = get_messaging_engine()
    messaging_metadata.create_all(engine)


@contextmanager
def get_messaging_session() -> Iterator[Session]:
    with Session(get_messaging_engine()) as session:
        yield session
