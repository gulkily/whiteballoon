from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import MetaData, UniqueConstraint
from sqlmodel import Field, SQLModel

hub_feed_metadata = MetaData()


class HubFeedBase(SQLModel):
    __abstract__ = True
    metadata = hub_feed_metadata


class HubFeedManifest(HubFeedBase, table=True):
    __tablename__ = "hub_feed_manifest"

    id: Optional[int] = Field(default=None, primary_key=True)
    peer_name: str = Field(index=True)
    manifest_digest: str = Field(index=True, unique=True)
    signed_at: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bundle_updated_at: datetime | None = None


class HubFeedRequest(HubFeedBase, table=True):
    __tablename__ = "hub_feed_request"
    __table_args__ = (
        UniqueConstraint("source_request_id", "source_instance", name="uq_hub_feed_request_source"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    peer_name: str = Field(index=True)
    manifest_digest: str = Field(index=True)
    source_request_id: int
    source_instance: str
    title: str
    description: str
    status: str = Field(index=True)
    sync_scope: str = Field(index=True)
    contact_email: str | None = None
    created_by_id: int | None = None
    created_by_username: str | None = None
    updated_at: datetime = Field(index=True)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment_count: int = 0
    last_comment_at: datetime | None = None


class HubFeedComment(HubFeedBase, table=True):
    __tablename__ = "hub_feed_comment"
    __table_args__ = (
        UniqueConstraint(
            "source_request_id",
            "source_comment_id",
            "source_instance",
            name="uq_hub_feed_comment_source",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: Optional[int] = Field(default=None, foreign_key="hub_feed_request.id", index=True)
    peer_name: str = Field(index=True)
    manifest_digest: str = Field(index=True)
    source_instance: str
    source_request_id: int
    source_comment_id: int
    username: str | None = None
    body: str
    sync_scope: str = Field(index=True)
    created_at: datetime = Field(index=True)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
