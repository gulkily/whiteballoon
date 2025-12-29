from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from app.config import get_settings
from app.modules.messaging import services as messaging_services
from app.models import User, UserSession
from app.skins.runtime import register_skin_helpers

templates = Jinja2Templates(directory="templates")
register_skin_helpers(templates)
templates.env.globals["feature_nav_status_tags"] = get_settings().feature_nav_status_tags


def site_title() -> str:
    return get_settings().site_title


templates.env.globals["site_title"] = site_title


def messaging_feature_enabled() -> bool:
    return get_settings().messaging_enabled


templates.env.globals["messaging_feature_enabled"] = messaging_feature_enabled


def messaging_unread_count(user_id: int | None) -> int:
    if not user_id or not get_settings().messaging_enabled:
        return 0
    try:
        summaries = messaging_services.list_threads_for_user(user_id)
    except Exception:
        return 0
    total = 0
    for summary in summaries:
        viewer_participant = next((p for p in summary.participants if p.user_id == user_id), None)
        if viewer_participant and viewer_participant.unread_count:
            total += viewer_participant.unread_count
    return total


templates.env.globals["messaging_unread_count"] = messaging_unread_count


def _parse_iso_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def friendly_time(value: Union[str, datetime, None]) -> str:
    dt = _parse_iso_datetime(value)
    if dt is None:
        return ""

    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    seconds = int(delta.total_seconds())

    suffix = "ago"
    if seconds < 0:
        seconds = abs(seconds)
        suffix = "from now"

    if seconds < 45:
        return "just now" if suffix == "ago" else "in a moment"
    if seconds < 90:
        return f"1 minute {suffix}"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minutes {suffix}"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"

    days = hours // 24
    if days == 1:
        return "yesterday" if suffix == "ago" else "tomorrow"
    if days < 7:
        return f"{days} days {suffix}"

    weeks = days // 7
    if weeks < 5:
        return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"

    local_now = datetime.now().astimezone()
    local_dt = dt.astimezone(local_now.tzinfo)
    if local_dt.year == local_now.year:
        return local_dt.strftime("%b %d at %I:%M %p")
    return local_dt.strftime("%b %d, %Y %I:%M %p")


def render_multiline(value: Optional[str], default: str = "") -> Markup:
    text = value if value and value.strip() else default
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = (
        normalized.replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
    )
    lines = normalized.split("\n")
    escaped_lines = [escape(line) for line in lines if line]
    if not escaped_lines:
        return Markup("")
    return Markup("<br />").join(escaped_lines)


templates.env.filters["friendly_time"] = friendly_time
templates.env.filters["render_multiline"] = render_multiline


def describe_session_role(user: User, session: Optional[UserSession]) -> Optional[dict[str, str]]:
    if not session:
        return None

    if not session.is_fully_authenticated:
        label = "Admin (pending verification)" if user.is_admin else "Pending verification"
        return {"label": label, "tone": "warning"}

    if user.is_admin:
        return {"label": "Administrator", "tone": "accent"}

    return {"label": "Member", "tone": "muted"}


__all__ = ["describe_session_role", "friendly_time", "render_multiline", "templates"]
