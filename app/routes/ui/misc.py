"""Miscellaneous UI routes that do not yet fit another module."""

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.url_utils import get_base_url

router = APIRouter(tags=["ui"])


def _format_bool(value: bool) -> str:
    return "enabled" if value else "disabled"


def _build_llms_text(request: Request) -> str:
    settings = get_settings()
    base_url = get_base_url(request)
    skins_allowed = ", ".join(settings.skins_allowed) if settings.skins_allowed else "none"
    lines = [
        "# WhiteBalloon /llms.txt",
        f"title: {settings.site_title}",
        f"base_url: {base_url}",
        "",
        "## How to engage",
        "- Use the same public UI and API routes as human users.",
        "- Auth is invite-only after the first account; login uses a verification code.",
        "- Session cookie: wb_session_id (do not forge or reuse outside this instance).",
        "",
        "## UI routes (public unless noted)",
        "- /",
        "- /auth/login",
        "- /auth/register",
        "- /settings/account",
        "- /settings/notifications (RSS tokens live here)",
        "- /invite/new",
        "- /invite/map",
        "- /members",
        "- /people/{username}",
        "- /admin (admin only)",
        "- /admin/sync-control (admin only)",
        "- /sync/public (admin only)",
        "- /sync/scope (admin only)",
    ]
    if settings.messaging_enabled:
        lines.append("- /messages (messaging enabled)")
    else:
        lines.append("- /messages (messaging disabled)")
    lines.extend(
        [
            "",
            "## API routes",
            "- GET /api/requests",
            "- GET /api/requests/pending",
            "- POST /api/requests",
            "- POST /api/requests/{id}/complete",
            "- POST /auth/register",
            "- POST /auth/login",
            "- POST /auth/login/verify",
            "- POST /auth/logout",
            "- POST /auth/invites (admin/session-user)",
            "",
            "## RSS",
            "- /feeds/<token>/<category>.xml",
            "",
            "## Features (runtime)",
            f"- messaging: {_format_bool(settings.messaging_enabled)}",
            f"- skins: {_format_bool(settings.skins_enabled)}",
            f"- skins_default: {settings.skin_default}",
            f"- skins_allowed: {skins_allowed}",
            f"- skins_preview: {_format_bool(settings.skin_preview_enabled)}",
            f"- skins_strict: {_format_bool(settings.skin_strict)}",
            f"- request_channels: {_format_bool(settings.request_channels_enabled)}",
            f"- contact_email: {_format_bool(settings.enable_contact_email)}",
            f"- comment_insights_indicator: {_format_bool(settings.comment_insights_indicator_enabled)}",
            f"- profile_signal_glaze: {_format_bool(settings.profile_signal_glaze_enabled)}",
            f"- peer_auth_queue: {_format_bool(settings.feature_peer_auth_queue)}",
            f"- self_auth: {_format_bool(settings.feature_self_auth)}",
            f"- nav_status_tags: {_format_bool(settings.feature_nav_status_tags)}",
            "",
            "## Docs",
            "- README.md",
            "- docs/spec.md",
            "",
            "## Safety",
            "- This file never includes secrets, API keys, or private tokens.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


@router.get("/llms.txt", include_in_schema=False)
def llms_txt(request: Request) -> PlainTextResponse:
    return PlainTextResponse(_build_llms_text(request))
