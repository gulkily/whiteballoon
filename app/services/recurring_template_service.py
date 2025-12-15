from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    RecurringRequestDeliveryMode,
    RecurringRequestRun,
    RecurringRequestTemplate,
    RequestAttribute,
)

RECURRING_TEMPLATE_ATTRIBUTE_KEY = "recurring_template_id"


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


def list_due_templates(
    session: Session,
    *,
    limit: int = 50,
) -> list[RecurringRequestTemplate]:
    now = datetime.utcnow()
    statement = (
        select(RecurringRequestTemplate)
        .where(RecurringRequestTemplate.paused.is_(False))
        .where(RecurringRequestTemplate.next_run_at.is_not(None))
        .where(RecurringRequestTemplate.next_run_at <= now)
        .order_by(RecurringRequestTemplate.next_run_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


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


def tag_request_with_template(
    session: Session,
    *,
    request_id: int,
    template_id: int,
) -> None:
    statement = select(RequestAttribute).where(
        RequestAttribute.request_id == request_id,
        RequestAttribute.key == RECURRING_TEMPLATE_ATTRIBUTE_KEY,
    )
    attribute = session.exec(statement).first()
    value = str(template_id)
    now = datetime.utcnow()
    if attribute:
        attribute.value = value
        attribute.updated_at = now
    else:
        attribute = RequestAttribute(
            request_id=request_id,
            key=RECURRING_TEMPLATE_ATTRIBUTE_KEY,
            value=value,
            created_at=now,
            updated_at=now,
        )
    session.add(attribute)
    session.commit()


def load_template_metadata(
    session: Session,
    request_ids: list[int],
) -> dict[int, dict[str, object]]:
    if not request_ids:
        return {}
    attribute_rows = session.exec(
        select(RequestAttribute)
        .where(RequestAttribute.request_id.in_(request_ids))
        .where(RequestAttribute.key == RECURRING_TEMPLATE_ATTRIBUTE_KEY)
    ).all()
    template_ids = {int(attr.value) for attr in attribute_rows if attr.value and attr.value.isdigit()}
    if not template_ids:
        return {}
    templates = session.exec(
        select(RecurringRequestTemplate).where(RecurringRequestTemplate.id.in_(template_ids))
    ).all()
    template_lookup = {template.id: template for template in templates if template.id}
    result: dict[int, dict[str, object]] = {}
    for attr in attribute_rows:
        try:
            template_id = int(attr.value)
        except (ValueError, TypeError):
            continue
        template = template_lookup.get(template_id)
        if not template:
            continue
        result[attr.request_id] = {
            "template_id": template.id,
            "template_title": template.title or "Untitled template",
        }
    return result


def record_run(
    session: Session,
    *,
    template_id: int,
    request_id: int | None,
    status_value: str,
    error_message: str | None = None,
) -> None:
    run = RecurringRequestRun(
        template_id=template_id,
        request_id=request_id,
        status=status_value,
        error_message=error_message,
    )
    session.add(run)
    session.commit()
