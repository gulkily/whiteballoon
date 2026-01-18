# Consistent Display Names – Step 2: Feature Description

**Problem**: Request headers, admin lists, and other templates still show raw usernames (`@handle` or “Community member”) even though chats/comments already leverage richer Signal display names. The mismatch confuses members and makes it harder to spot who’s who across pages like `/requests/39` versus `/requests/30`.

## User stories
- As a member reading a request detail page, I want the requester’s name to match the chat bubbles (display name + profile link) so I immediately recognize them.
- As an admin browsing ledger/profile screens, I want a reusable username component so every list renders identities consistently without hand-rolled markup.
- As a developer, I want a single include/helper for display names so future pages automatically stay in sync with UX conventions.

## Core requirements
- Create a templated component (e.g., `partials/display_name.html`) or macro that renders: display name when available, falls back to `@username`, wraps in an optional `/people/<username>` link, and accepts CSS class modifiers.
- Thread the existing Signal display-name lookup (Option A from Step 1) into request metadata so the component can consume it in headers, cards, and admin tables.
- Inventory and update every template that currently prints `@{{ username }}` or similar (initial list: `requests/detail.html`, `requests/partials/item.html`, `partials/comment_card.html`, `partials/account_nav.html`, `browse/index.html`, `members/index.html`, `sync/public.html`, `admin/ledger.html`, `admin/profile_detail.html`, `admin/profiles.html`, `peer_auth/partials/list.html`, `invite/map.html`, `partials/account_nav.html`, etc.).
- Ensure the component gracefully handles anonymous/community cases without broken links.
- No changes to how display names are stored—reuse existing `signal_display_name:<slug>` attributes only.

## Shared component inventory
- `templates/requests/partials/channel_message.html`: already shows display names; use this as the reference styling and data contract.
- `templates/partials/comment_card.html`: will adopt the new component.
- `templates/partials/account_nav.html` and other nav/browse cards: update to call the component instead of embedding `@{{ user.username }}`.
- Backend context helpers (`app/routes/ui/helpers.py`, `_build_request_detail_context`) already expose `comment_display_names`; we’ll extend them to provide requester display info but avoid duplicating logic.

## Simple user flow
1. Backend populates `display_name` + `username` for each person rendered on a page.
2. Template calls the shared component, passing `username`, optional `display_name`, `href`, and custom classes.
3. Component renders the display name (or `@username` fallback) with the link and consistent tooltip.
4. User navigates across pages (/requests, /members, admin lists) and sees the same identity format everywhere.

## Success criteria
- Every template identified in the inventory renders people via the new component (spot-check `/requests/39`, `/requests/30`, `/members`, `/browse`, `/admin/ledger`, `/peer-auth`).
- Display names render when available; otherwise we see `@username` with a working profile link.
- No regressions in chat/comment rendering since they already follow the desired format.
- Developers reference the component instead of reinventing markup in future PRs.
