from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HubFeedCommentDTO(BaseModel):
    id: int
    request_id: int
    username: Optional[str]
    body: str
    created_at: datetime
    source_instance: str


class HubFeedRequestDTO(BaseModel):
    id: int
    peer_name: str
    manifest_digest: str
    source_request_id: int
    source_instance: str
    title: str
    description: str
    status: str
    sync_scope: str
    contact_email: Optional[str]
    created_by_id: Optional[int]
    created_by_username: Optional[str]
    updated_at: datetime
    last_comment_at: Optional[datetime]
    comment_count: int
    comments: List[HubFeedCommentDTO] = Field(default_factory=list)


class HubFeedPageDTO(BaseModel):
    items: list[HubFeedRequestDTO]
    next_offset: Optional[int]
    total: int
