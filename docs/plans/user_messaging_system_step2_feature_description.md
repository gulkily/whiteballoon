# User Messaging System – Step 2 Feature Description

## Problem
Members currently have no way to coordinate directly, forcing every follow-up into the public request/comments surfaces. We need a private messaging capability that admins can enable per instance while ensuring the entire message ledger lives in an isolated database for compliance and future scaling.

## User stories
- As a fully authenticated member, I want to send a direct message from someone’s profile so we can coordinate privately without leaving WhiteBalloon.
- As the recipient, I want to receive, read, and reply to new messages from the dashboard so I can keep context next to my requests and invites.
- As an administrator, I want to toggle messaging on/off from the existing admin controls so I can defer rollout or disable it during incidents.
- As an operator, I want the messaging data stored in a dedicated database so exports, backups, and retention policies stay isolated from the primary app data.

## Core requirements
- Messaging is only available when an admin-level toggle is enabled; the default state is disabled.
- Every message record is persisted in a separate database/engine with its own backup cadence, while the primary database stores only references needed for routing/permissions.
- UI/UX honors the current modular SSR pattern (no SPA frameworks) and reuses existing auth/session context for permissions.
- Members can start conversations from profile views or a future inbox entry point, with unread counts reflected in the nav/dashboard.
- Admins can review high-level operational metrics (enabled status, storage health) without accessing message contents.

## Shared component inventory
- `templates/profile/*.html` – extend to surface “Message” actions because profiles already convey trust context.
- `templates/base.html` nav + dashboard partials – reuse existing notification badge patterns for an inbox link.
- `/admin/settings` (or existing admin scope toggle panel) – reuse the canonical feature-flag UI so operators toggle messaging alongside other sync/privacy controls.
- `User` + `Session` models/services – reused for identity/auth context; no new auth stack.
- `./wb` CLI + admin dashboards – reuse for seeding the messaging database (init/backups) to avoid new operational entry points.

## Simple user flow
1. Admin enables “Direct messaging” from the existing admin controls; CLI/script initializes the separate messaging database if needed.
2. A fully authenticated member opens another member’s profile and presses “Message.”
3. The member writes and sends a message; the backend writes to the dedicated messaging database and adds metadata to the main DB for unread counts.
4. The recipient sees an inbox badge on the dashboard/nav, opens the inbox view, and reads/replies.
5. Messages stay accessible until manually deleted per future retention policies, with backups managed independently of the primary DB.

## Success criteria
- Messaging toggle defaults to off and can be flipped by admins within one click of existing settings; telemetry confirms the state change.
- ≥95% of message send/receive requests complete within the same latency budget as existing request comments (<500 ms p95).
- Verification that all message rows exist only in the dedicated database (spot-checked via CLI/metrics) during testing.
- Inbox entry point drives at least one successful message exchange in staged QA scenarios without breaking existing profile or dashboard flows.
