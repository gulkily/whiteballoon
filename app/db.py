from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

# Import models so SQLModel metadata is populated when this module loads.
from app import models  # noqa: F401


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    database_url = settings.database_url
    connect_args: dict[str, object] = {}

    url = make_url(database_url)
    if url.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        Path(url.database or "data/app.db").parent.mkdir(parents=True, exist_ok=True)

    return create_engine(database_url, echo=False, connect_args=connect_args)


def reset_engine() -> None:
    get_engine.cache_clear()


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
