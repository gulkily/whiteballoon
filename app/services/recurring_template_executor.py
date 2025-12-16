from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlmodel import Session

from app.models import (
    HELP_REQUEST_STATUS_DRAFT,
    HELP_REQUEST_STATUS_OPEN,
    RecurringRequestDeliveryMode,
    RecurringRequestTemplate,
    User,
)
from app.modules.requests import services as request_services
from app.services import recurring_template_service

logger = logging.getLogger(__name__)


def process_due_templates(session: Session, templates: list[RecurringRequestTemplate]) -> int:
    """Create drafts or published requests for each due template."""
    processed = 0
    for template in templates:
        try:
            _process_template(session, template)
            processed += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            session.rollback()
            logger.exception("Failed to process recurring template %s", template.id)
            _mark_template_error(session, template, str(exc))
    return processed


def _process_template(session: Session, template: RecurringRequestTemplate) -> None:
    owner = session.get(User, template.created_by_user_id)
    if not owner:
        raise RuntimeError(f"Template owner {template.created_by_user_id} not found")

    status_value = (
        HELP_REQUEST_STATUS_OPEN
        if template.delivery_mode == RecurringRequestDeliveryMode.publish
        else HELP_REQUEST_STATUS_DRAFT
    )

    new_request = request_services.create_request(
        session,
        user=owner,
        description=template.description,
        contact_email=template.contact_email_override,
        status_value=status_value,
    )
    if new_request.id:
        recurring_template_service.tag_request_with_template(
            session,
            request_id=new_request.id,
            template_id=template.id,
        )

    now = datetime.utcnow()
    template.last_run_at = now
    template.last_error = None
    template.next_run_at = _calculate_next_run(template, now)
    template.updated_at = now
    session.add(template)
    session.commit()

    recurring_template_service.record_run(
        session,
        template_id=template.id,
        request_id=new_request.id,
        status_value="success",
    )

    logger.info(
        "Recurring template %s generated a %s request",
        template.id,
        template.delivery_mode.value,
    )


def _calculate_next_run(template: RecurringRequestTemplate, reference: datetime) -> datetime:
    if template.interval_minutes <= 0:
        # Fallback to at least one hour to avoid tight loops
        interval = timedelta(hours=1)
    else:
        interval = timedelta(minutes=template.interval_minutes)

    next_run = template.next_run_at or reference
    while next_run <= reference:
        next_run = next_run + interval
    return next_run


def _mark_template_error(session: Session, template: RecurringRequestTemplate, message: str) -> None:
    template.last_error = message[:500]
    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    recurring_template_service.record_run(
        session,
        template_id=template.id,
        request_id=None,
        status_value="error",
        error_message=message[:500],
    )
