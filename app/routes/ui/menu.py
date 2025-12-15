from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates

router = APIRouter(tags=["ui"])


def _build_link(
    *,
    title: str,
    description: str,
    href: str,
    requires_full: bool = False,
    admin_only: bool = False,
) -> dict[str, object]:
    return {
        "title": title,
        "description": description,
        "href": href,
        "requires_full": requires_full,
        "admin_only": admin_only,
    }


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

    sections = [
        {
            "title": "Community",
            "description": "Everyday destinations for members.",
            "links": [
                _build_link(
                    title="Requests feed",
                    description="Catch up on every open help request and share your own.",
                    href="/requests",
                ),
                _build_link(
                    title="Members directory",
                    description="Browse people who have opted into sharing and folks you invited.",
                    href="/members",
                    requires_full=True,
                ),
                _build_link(
                    title="Invite map",
                    description="Visualize your branch of the invite tree and extended network.",
                    href="/invite/map",
                    requires_full=True,
                ),
                _build_link(
                    title="Request channels",
                    description="Live chat view of every help request with unread indicators.",
                    href="/requests/channels",
                    requires_full=True,
                ),
                _build_link(
                    title="Send Welcome",
                    description="Generate invite links, personalized notes, and onboarding tips.",
                    href="/invite/new",
                    requires_full=True,
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
                ),
                _build_link(
                    title="Settings",
                    description="Update contact email, auth details, and personal data.",
                    href="/settings/account",
                ),
            ],
        },
    ]

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
                    ),
                    _build_link(
                        title="Profile directory",
                        description="Review every account’s contact info, sharing scope, and requests.",
                        href="/admin/profiles",
                        admin_only=True,
                    ),
                    _build_link(
                        title="Sync control",
                        description="Manage peers, queue push/pull jobs, and inspect activity logs.",
                        href="/admin/sync-control",
                        admin_only=True,
                    ),
                    _build_link(
                        title="Comment insights",
                        description="Browse AI summaries/tags for request comments.",
                        href="/admin/comment-insights",
                        admin_only=True,
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

    context = {
        "request": request,
        "session": session,
        "session_role": describe_session_role(user, session),
        "session_username": user.username,
        "session_avatar_url": session_user.avatar_url,
        "user": user,
        "menu_sections": sections,
    }
    return templates.TemplateResponse("menu/index.html", context)


__all__ = ["router"]
