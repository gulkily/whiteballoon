from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.models import RecurringRequestDeliveryMode
from app.routes.ui.helpers import describe_session_role, get_account_avatar, templates
from app.services import recurring_template_service

router = APIRouter(tags=["ui"])


@router.get("/requests/recurring")
def recurring_requests_page(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    viewer = session_user.user
    session_record = session_user.session
    template_list = recurring_template_service.list_templates_for_user(db, user_id=viewer.id)
    delivery_modes = list(RecurringRequestDeliveryMode)
    interval_options = _recurring_interval_options()
    prepared_templates: list[dict[str, object]] = []
    for template in template_list:
        preset = _match_interval_preset(template.interval_minutes)
        custom_value, custom_unit = _minutes_to_custom_interval(template.interval_minutes)
        prepared_templates.append(
            {
                "record": template,
                "interval_preset": preset,
                "custom_interval_value": custom_value,
                "custom_interval_unit": custom_unit,
            }
        )
    context = {
        "request": request,
        "user": viewer,
        "session": session_record,
        "session_role": describe_session_role(viewer, session_record),
        "session_username": viewer.username,
        "session_avatar_url": get_account_avatar(db, viewer.id),
        "templates": prepared_templates,
        "delivery_modes": delivery_modes,
        "interval_options": interval_options,
    }
    return templates.TemplateResponse("requests/recurring.html", context)


@router.post("/requests/recurring")
def create_recurring_template(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    *,
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[str, Form(...)],
    contact_email_override: Annotated[Optional[str], Form()] = None,
    delivery_mode: Annotated[str, Form()] = RecurringRequestDeliveryMode.draft.value,
    interval_preset: Annotated[Optional[str], Form()] = None,
    custom_interval_value: Annotated[Optional[int], Form()] = None,
    custom_interval_unit: Annotated[Optional[str], Form()] = "days",
    next_run_at: Annotated[Optional[str], Form()] = None,
):
    delivery = _parse_delivery_mode(delivery_mode)
    next_run = _parse_datetime_local(next_run_at)
    interval_minutes = _resolve_interval_minutes(
        interval_preset,
        custom_interval_value,
        custom_interval_unit,
    )
    recurring_template_service.create_template(
        db,
        user_id=session_user.user.id,
        title=title,
        description=description,
        contact_email_override=contact_email_override,
        delivery_mode=delivery,
        interval_minutes=interval_minutes,
        next_run_at=next_run,
    )
    return RedirectResponse(url="/requests/recurring", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/recurring/{template_id}/action")
def recurring_template_action(
    template_id: int,
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
    *,
    action: Annotated[str, Form(...)],
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    contact_email_override: Annotated[Optional[str], Form()] = None,
    delivery_mode: Annotated[Optional[str], Form()] = None,
    interval_preset: Annotated[Optional[str], Form()] = None,
    custom_interval_value: Annotated[Optional[int], Form()] = None,
    custom_interval_unit: Annotated[Optional[str], Form()] = None,
    next_run_at: Annotated[Optional[str], Form()] = None,
):
    template = recurring_template_service.get_template_for_user(
        db,
        template_id=template_id,
        user_id=session_user.user.id,
    )
    action_value = action.lower().strip()
    if action_value == "delete":
        recurring_template_service.delete_template(db, template=template)
    elif action_value == "pause":
        recurring_template_service.update_template(db, template=template, paused=True)
    elif action_value == "resume":
        recurring_template_service.update_template(db, template=template, paused=False)
    elif action_value == "edit":
        mode = _parse_delivery_mode(delivery_mode) if delivery_mode else None
        next_run = _parse_datetime_local(next_run_at)
        resolved_interval = None
        if interval_preset or custom_interval_value is not None:
            resolved_interval = _resolve_interval_minutes(
                interval_preset,
                custom_interval_value,
                custom_interval_unit,
            )
        recurring_template_service.update_template(
            db,
            template=template,
            title=title,
            description=description,
            contact_email_override=contact_email_override,
            delivery_mode=mode,
            interval_minutes=resolved_interval,
            next_run_at=next_run,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown action")
    return RedirectResponse(url="/requests/recurring", status_code=status.HTTP_303_SEE_OTHER)


def _parse_delivery_mode(value: str | None) -> RecurringRequestDeliveryMode:
    if not value:
        return RecurringRequestDeliveryMode.draft
    try:
        return RecurringRequestDeliveryMode(value)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid delivery mode") from error


def _parse_datetime_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date/time") from error


def _resolve_interval_minutes(
    interval_preset: str | None,
    custom_value: int | None,
    custom_unit: str | None,
) -> int:
    if interval_preset:
        try:
            minutes = int(interval_preset)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid interval preset") from error
        if minutes <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")
        return minutes

    if not custom_value or custom_value <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Custom interval must be positive")
    unit = (custom_unit or "minutes").lower()
    unit_map = {
        "minutes": 1,
        "hours": 60,
        "days": 1440,
        "weeks": 10080,
    }
    if unit not in unit_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid interval unit")
    minutes = custom_value * unit_map[unit]
    if minutes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Interval must be positive")
    return minutes


def _recurring_interval_options() -> list[dict[str, str]]:
    return [
        {"value": "1440", "label": "Daily"},
        {"value": "2880", "label": "Every 2 days"},
        {"value": "10080", "label": "Weekly"},
        {"value": "20160", "label": "Every 2 weeks"},
    ]


def _match_interval_preset(minutes: int) -> str | None:
    for option in _recurring_interval_options():
        if minutes == int(option["value"]):
            return option["value"]
    return None


def _minutes_to_custom_interval(minutes: int) -> tuple[int, str]:
    for unit, factor in (("weeks", 10080), ("days", 1440), ("hours", 60)):
        if minutes % factor == 0:
            return minutes // factor, unit
    return minutes, "minutes"
