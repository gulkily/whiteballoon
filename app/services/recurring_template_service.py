from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    RecurringRequestDeliveryMode,
    RecurringRequestTemplate,
)


def list_templates_for_user(session: Session, *, user_id: int) -> list[RecurringRequestTemplate]:
    statement = (
        select(RecurringRequestTemplate)
        .where(RecurringRequestTemplate.created_by_user_id == user_id)
        .order_by(RecurringRequestTemplate.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_template_for_user(
    session: Session,
    *,
    template_id: int,
    user_id: int,
) -> RecurringRequestTemplate:
    template = session.get(RecurringRequestTemplate, template_id)
    if not template or template.created_by_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


def create_template(
    session: Session,
    *,
    user_id: int,
    title: str | None,
    description: str,
    contact_email_override: str | None,
    delivery_mode: RecurringRequestDeliveryMode,
    interval_minutes: int,
    next_run_at: datetime | None = None,
) -> RecurringRequestTemplate:
    if interval_minutes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")

    scheduled_time = next_run_at or (datetime.utcnow())
    template = RecurringRequestTemplate(
        created_by_user_id=user_id,
        title=title or None,
        description=description.strip(),
        contact_email_override=(contact_email_override or None),
        delivery_mode=delivery_mode,
        interval_minutes=interval_minutes,
        next_run_at=scheduled_time,
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def update_template(
    session: Session,
    *,
    template: RecurringRequestTemplate,
    title: str | None = None,
    description: str | None = None,
    contact_email_override: str | None = None,
    delivery_mode: RecurringRequestDeliveryMode | None = None,
    interval_minutes: int | None = None,
    next_run_at: datetime | None = None,
    paused: bool | None = None,
    last_error: str | None = None,
) -> RecurringRequestTemplate:
    if interval_minutes is not None and interval_minutes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")

    if title is not None:
        template.title = title or None
    if description is not None:
        template.description = description.strip()
    if contact_email_override is not None:
        template.contact_email_override = contact_email_override or None
    if delivery_mode is not None:
        template.delivery_mode = delivery_mode
    if interval_minutes is not None:
        template.interval_minutes = interval_minutes
    if next_run_at is not None:
        template.next_run_at = next_run_at
    if paused is not None:
        template.paused = paused
    if last_error is not None:
        template.last_error = last_error or None

    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def delete_template(session: Session, *, template: RecurringRequestTemplate) -> None:
    session.delete(template)
    session.commit()
