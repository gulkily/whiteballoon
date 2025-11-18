from __future__ import annotations

from fastapi import APIRouter, Query

from .schema import HubFeedPageDTO
from .service import DEFAULT_FEED_PAGE_SIZE, list_feed_requests

router = APIRouter(prefix="/api/v1/feed", tags=["hub-feed"])


@router.get("/", response_model=HubFeedPageDTO)
def read_feed(
    limit: int = Query(DEFAULT_FEED_PAGE_SIZE, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> HubFeedPageDTO:
    return list_feed_requests(limit=limit, offset=offset)
