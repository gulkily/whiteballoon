from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal, Sequence

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.config import get_settings
from app.models import HELP_REQUEST_STATUS_DRAFT, HelpRequest, RequestAttribute, User

PIN_ATTRIBUTE_KEY = "pin"


@dataclass(slots=True)
class PinMetadata:
    rank: int
    pinned_by_user_id: int | None
    pinned_at: datetime | None


@dataclass(slots=True)
class PinnedRequest:
    request: HelpRequest
    metadata: PinMetadata


_settings = get_settings()


def _load_pin_metadata(attribute: RequestAttribute) -> PinMetadata | None:
    if not attribute.value:
        return None
    try:
        payload = json.loads(attribute.value)
    except json.JSONDecodeError:
        return None
    rank = int(payload.get("rank", 0))
    pinned_by = payload.get("pinned_by")
    pinned_at_raw = payload.get("pinned_at")
    pinned_at = None
    if isinstance(pinned_at_raw, str):
        try:
            pinned_at = datetime.fromisoformat(pinned_at_raw)
        except ValueError:
            pinned_at = None
    return PinMetadata(rank=rank, pinned_by_user_id=pinned_by, pinned_at=pinned_at)


def _serialize_pin_value(
    rank: int,
    *,
    actor_id: int | None,
    pinned_at: datetime | None = None,
) -> str:
    payload = {
        "rank": rank,
        "pinned_by": actor_id,
        "pinned_at": (pinned_at or datetime.utcnow()).isoformat(),
    }
    return json.dumps(payload)


def list_pin_attributes(session: Session) -> Sequence[RequestAttribute]:
    statement = select(RequestAttribute).where(RequestAttribute.key == PIN_ATTRIBUTE_KEY)
    return list(session.exec(statement).all())


def count_pins(session: Session) -> int:
    statement = select(RequestAttribute.id).where(RequestAttribute.key == PIN_ATTRIBUTE_KEY)
    return len(session.exec(statement).all())


def list_pinned_requests(session: Session, *, limit: int | None = None) -> list[PinnedRequest]:
    statement = (
        select(RequestAttribute, HelpRequest)
        .join(HelpRequest, HelpRequest.id == RequestAttribute.request_id)
        .where(RequestAttribute.key == PIN_ATTRIBUTE_KEY)
        .where(HelpRequest.status != HELP_REQUEST_STATUS_DRAFT)
    )
    rows = session.exec(statement).all()
    records: list[PinnedRequest] = []
    for attribute, help_request in rows:
        metadata = _load_pin_metadata(attribute)
        if metadata is None:
            continue
        records.append(PinnedRequest(request=help_request, metadata=metadata))
    records.sort(
        key=lambda record: (
            record.metadata.rank,
            -(record.request.created_at.timestamp() if record.request.created_at else 0),
        )
    )
    if limit is None:
        return records
    return records[:limit]


def get_pin_map(session: Session) -> dict[int, PinMetadata]:
    pins = {}
    for attribute in list_pin_attributes(session):
        metadata = _load_pin_metadata(attribute)
        if metadata is None:
            continue
        pins[attribute.request_id] = metadata
    return pins


def request_is_pinned(session: Session, request_id: int) -> bool:
    statement = select(RequestAttribute).where(
        RequestAttribute.request_id == request_id,
        RequestAttribute.key == PIN_ATTRIBUTE_KEY,
    )
    return session.exec(statement).first() is not None


def ensure_capacity(session: Session) -> None:
    limit = _settings.pinned_requests_limit
    if limit <= 0:
        return
    current = count_pins(session)
    if current >= limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {limit} pinned requests reached.",
        )


def _next_rank(session: Session) -> int:
    attributes = list_pin_attributes(session)
    if not attributes:
        return 1
    ranks = []
    for attribute in attributes:
        metadata = _load_pin_metadata(attribute)
        if metadata is not None:
            ranks.append(metadata.rank)
    return (max(ranks) + 1) if ranks else 1


def set_pin(
    session: Session,
    *,
    request: HelpRequest,
    actor: User,
    rank: int | None = None,
) -> None:
    statement = select(RequestAttribute).where(
        RequestAttribute.request_id == request.id,
        RequestAttribute.key == PIN_ATTRIBUTE_KEY,
    )
    attribute = session.exec(statement).first()
    resolved_rank = rank if rank is not None else _next_rank(session)
    payload = _serialize_pin_value(resolved_rank, actor_id=actor.id)
    now = datetime.utcnow()
    if attribute:
        attribute.value = payload
        attribute.updated_at = now
        attribute.updated_by_user_id = actor.id
        session.add(attribute)
    else:
        attribute = RequestAttribute(
            request_id=request.id,
            key=PIN_ATTRIBUTE_KEY,
            value=payload,
            created_at=now,
            updated_at=now,
            created_by_user_id=actor.id,
            updated_by_user_id=actor.id,
        )
        session.add(attribute)
    session.commit()


def clear_pin(session: Session, *, request_id: int) -> None:
    statement = select(RequestAttribute).where(
        RequestAttribute.request_id == request_id,
        RequestAttribute.key == PIN_ATTRIBUTE_KEY,
    )
    attribute = session.exec(statement).first()
    if not attribute:
        return
    session.delete(attribute)
    session.commit()


def update_pin_rank(session: Session, *, request_id: int, new_rank: int) -> None:
    statement = select(RequestAttribute).where(
        RequestAttribute.request_id == request_id,
        RequestAttribute.key == PIN_ATTRIBUTE_KEY,
    )
    attribute = session.exec(statement).first()
    if not attribute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pin not found")
    payload = _load_pin_metadata(attribute)
    if payload is None:
        payload = PinMetadata(rank=new_rank, pinned_by_user_id=None, pinned_at=None)
    payload.rank = new_rank
    attribute.value = _serialize_pin_value(
        payload.rank,
        actor_id=payload.pinned_by_user_id,
        pinned_at=payload.pinned_at,
    )
    session.add(attribute)
    session.commit()


def shift_pin(session: Session, *, request_id: int, direction: Literal["up", "down"]) -> None:
    pins = list_pin_attributes(session)
    pins_with_meta = []
    for attribute in pins:
        metadata = _load_pin_metadata(attribute)
        if metadata is None:
            continue
        pins_with_meta.append((attribute, metadata))
    pins_with_meta.sort(key=lambda item: item[1].rank)
    target_index = next((idx for idx, (attr, _) in enumerate(pins_with_meta) if attr.request_id == request_id), None)
    if target_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pin not found")
    if direction == "up" and target_index == 0:
        return
    if direction == "down" and target_index == len(pins_with_meta) - 1:
        return
    swap_index = target_index - 1 if direction == "up" else target_index + 1
    target_attr, target_meta = pins_with_meta[target_index]
    swap_attr, swap_meta = pins_with_meta[swap_index]
    target_rank = target_meta.rank
    swap_rank = swap_meta.rank
    target_attr.value = _serialize_pin_value(
        swap_rank,
        actor_id=target_meta.pinned_by_user_id,
        pinned_at=target_meta.pinned_at,
    )
    swap_attr.value = _serialize_pin_value(
        target_rank,
        actor_id=swap_meta.pinned_by_user_id,
        pinned_at=swap_meta.pinned_at,
    )
    now = datetime.utcnow()
    target_attr.updated_at = now
    swap_attr.updated_at = now
    session.add(target_attr)
    session.add(swap_attr)
    session.commit()
