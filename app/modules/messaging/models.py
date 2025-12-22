from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import MetaData, UniqueConstraint
from sqlmodel import Field, SQLModel


messaging_metadata = MetaData()


class MessagingBase(SQLModel):
    __abstract__ = True
    metadata = messaging_metadata


class MessageThread(MessagingBase, table=True):
    __tablename__ = "message_threads"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_by_user_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latest_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class MessageParticipant(MessagingBase, table=True):
    __tablename__ = "message_participants"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_message_participants_thread_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: int = Field(foreign_key="message_threads.id", nullable=False, index=True)
    user_id: int = Field(nullable=False, index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_read_at: Optional[datetime] = Field(default=None)


class Message(MessagingBase, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: int = Field(foreign_key="message_threads.id", nullable=False, index=True)
    sender_user_id: int = Field(nullable=False, index=True)
    body: str = Field(nullable=False, max_length=4000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
