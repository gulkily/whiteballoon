from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.dependencies import SessionDep, SessionUser, require_session_user
from app.captions import build_caption_payload, load_preferences as load_caption_preferences
from app.routes.ui.helpers import describe_session_role, templates
from app.services import peer_auth_service

router = APIRouter(tags=["ui"])


def _build_link(
    *,
    title: str,
    description: str,
    href: str,
    requires_full: bool = False,
    admin_only: bool = False,
    icon: str | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "description": description,
        "href": href,
        "requires_full": requires_full,
        "admin_only": admin_only,
        "icon": icon,
    }


def _build_peer_ledger_link(settings):
    if not settings.feature_peer_auth_queue:
        return []
    return [
        _build_link(
            title="Peer auth ledger",
            description="Download the reviewer approval/denial log.",
            href="/admin/peer-auth/ledger",
            admin_only=True,
            icon="partials/icons/menu_admin_panel.svg",
        )
    ]


@router.get("/menu")
def site_menu(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
):
    user = session_user.user
    session = session_user.session
    is_full_session = session.is_fully_authenticated
    is_admin = user.is_admin
    is_peer_auth_reviewer = peer_auth_service.user_is_peer_auth_reviewer(db, user=user)

    sections = [
        {
            "title": "Community",
            "description": "Everyday destinations for members.",
            "links": [
                _build_link(
                    title="Requests workspace",
                    description="Catch up on every open help request, pin threads, and share your own.",
                    href="/requests/channels",
                    icon="partials/icons/nav_requests.svg",
                ),
                _build_link(
                    title="Members directory",
                    description="Browse people who have opted into sharing and folks you invited.",
                    href="/members",
                    requires_full=True,
                    icon="partials/icons/nav_browse.svg",
                ),
                _build_link(
                    title="Invite map",
                    description="Visualize your branch of the invite tree and extended network.",
                    href="/invite/map",
                    requires_full=True,
                    icon="partials/icons/menu_invite_map.svg",
                ),
                _build_link(
                    title="Request channels",
                    description="Live chat view of every help request with unread indicators.",
                    href="/requests/channels",
                    requires_full=True,
                    icon="partials/icons/menu_channels.svg",
                ),
                _build_link(
                    title="Send Welcome",
                    description="Generate invite links, personalized notes, and onboarding tips.",
                    href="/invite/new",
                    requires_full=True,
                    icon="partials/icons/menu_send_welcome.svg",
                ),
                _build_link(
                    title="Recurring requests",
                    description="Manage templates that auto-create chores or meeting reminders.",
                    href="/requests/recurring",
                    requires_full=True,
                    icon="partials/icons/menu_recurring.svg",
                ),
            ],
        },
        {
            "title": "Account",
            "description": "Manage your identity and see your status.",
            "links": [
                _build_link(
                    title="Profile",
                    description="Check your privileges, profile highlight, and contact info.",
                    href="/profile",
                    icon="partials/icons/menu_profile.svg",
                ),
                _build_link(
                    title="Settings",
                    description="Update contact email, auth details, and personal data.",
                    href="/settings/account",
                    icon="partials/icons/menu_settings.svg",
                ),
                _build_link(
                    title="Notifications & RSS",
                    description="Copy private feed URLs or rotate them when needed.",
                    href="/settings/notifications",
                    icon="partials/icons/menu_settings.svg",
                ),
            ],
        },
    ]

    settings = get_settings()

    if is_admin:
        sections.append(
            {
                "title": "Admin tools",
                "description": "Operator-only destinations for reviewing people, sync, and automation.",
                "links": [
                    _build_link(
                        title="Admin panel",
                        description="Jump to the control center for audits and tooling.",
                        href="/admin",
                        admin_only=True,
                        icon="partials/icons/menu_admin_panel.svg",
                    ),
                    _build_link(
                        title="Profile directory",
                        description="Review every account’s contact info, sharing scope, and requests.",
                        href="/admin/profiles",
                        admin_only=True,
                        icon="partials/icons/menu_profile_directory.svg",
                    ),
                    _build_link(
                        title="Sync control",
                        description="Manage peers, queue push/pull jobs, and inspect activity logs.",
                        href="/admin/sync-control",
                        admin_only=True,
                        icon="partials/icons/menu_sync_control.svg",
                    ),
                    _build_link(
                        title="Comment insights",
                        description="Browse AI summaries/tags for request comments.",
                        href="/admin/comment-insights",
                        admin_only=True,
                        icon="partials/icons/menu_comment_insights.svg",
                    ),
                    *_build_peer_ledger_link(settings),
                ],
            }
        )

    if is_peer_auth_reviewer and settings.feature_peer_auth_queue:
        sections.append(
            {
                "title": "Peer authentication",
                "description": "Review half-authenticated sessions waiting for confirmation.",
                "links": [
                    _build_link(
                        title="Review queue",
                        description="Inspect pending sessions, confirm 6-digit codes, and log approvals.",
                        href="/peer-auth",
                        requires_full=True,
                        icon="partials/icons/menu_admin_panel.svg",
                    ),
                ],
            }
        )

    for section in sections:
        filtered_links = []
        for link in section["links"]:
            requires_full = bool(link.get("requires_full"))
            admin_only = bool(link.get("admin_only"))
            if admin_only and not is_admin:
                continue
            disabled = False
            disabled_hint: Optional[str] = None
            if requires_full and not is_full_session:
                disabled = True
                disabled_hint = "Requires full session"
            filtered_links.append(
                {
                    **link,
                    "disabled": disabled,
                    "disabled_hint": disabled_hint,
                }
            )
        section["links"] = filtered_links

    caption_prefs = load_caption_preferences(db, user.id)
    context = {
        "request": request,
        "session": session,
        "session_role": describe_session_role(user, session),
        "session_username": user.username,
        "session_avatar_url": session_user.avatar_url,
        "user": user,
        "menu_sections": sections,
        "menu_caption": build_caption_payload(
            caption_prefs,
            caption_id="menu_intro",
            text="Jump anywhere in WhiteBalloon without crowding the main navigation.",
        ),
    }
    return templates.TemplateResponse("menu/index.html", context)


__all__ = ["router"]
