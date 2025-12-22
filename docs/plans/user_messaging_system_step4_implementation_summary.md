# User Messaging System – Step 4 Implementation Summary

## Stage 1 – Messaging database + models
- Changes:
  - Added `MESSAGING_DATABASE_URL` setting plus a dedicated messaging module package with SQLModel metadata bound to its own engine.
  - Introduced `MessageThread`, `MessageParticipant`, and `Message` models scoped to `data/messages.db`.
  - Created helper functions to initialize and access the messaging database without touching the primary app store.
- Verification:
  - Ran a Python harness (`python -m app.modules.messaging.db` init call) to initialize the database and confirmed `data/messages.db` contains the new tables.
- Notes:
  - Cross-database joins remain unsupported; denormalized user info will be handled at the service layer later.

## Stage 2 – Admin toggle + setup workflow
- Changes:
  - Added `ENABLE_DIRECT_MESSAGING` flag + dynamic settings reload so admins can flip messaging without restarts.
  - Exposed a direct-messaging card on `/sync/public` with a form that POSTs to the new `/admin/messaging/toggle` route, ensuring the messaging DB initializes automatically on enable.
  - Documented the dedicated DB path in `.env.example` and added `wb messaging init-db` to the CLI (plus wiring through `wb.py`) for operators who prefer the terminal workflow.
- Verification:
  - Ran `./wb messaging init-db` to ensure the CLI hook initializes `data/messages.db`.
  - Flipped `ENABLE_DIRECT_MESSAGING` on/off via a Python shell (`reset_settings_cache`) to confirm `get_settings().messaging_enabled` reflects changes immediately.
- Notes:
  - Toggle redirects back to `/sync/public` with a status alert so admins can see the outcome alongside existing sync controls.

## Stage 3 – Profile entry points + nav affordances
- Changes:
  - Registered a `messaging_feature_enabled()` helper so templates can react to the instance toggle without duplicating config plumbing.
  - Added inbox affordances to the global account nav (hidden until members are fully authenticated) with data attributes for upcoming unread-badge logic.
  - Surfaced “Message” buttons on `/people/{username}` and the members directory cards; both emit `data-messaging-launch`/`data-message-username` hooks for the upcoming composer.
- Verification:
  - Rendered `profile/show.html` via the template engine to confirm the new CTA renders without errors when messaging is enabled.
  - Manually inspected the nav/member templates to ensure the inbox link and card buttons are gated by `messaging_feature_enabled()` plus session checks, so they disappear when the toggle is off or viewers are half-authenticated.
- Notes:
  - Buttons currently act as launch affordances only; Stage 4 wires them to real compose endpoints.

## Stage 4 – Conversation creation + send endpoints
- Changes:
- Verification:
- Notes:

## Stage 5 – Inbox + thread views
- Changes:
- Verification:
- Notes:

## Stage 6 – Unread counts + notifications
- Changes:
- Verification:
- Notes:

## Stage 7 – Ops instrumentation + docs
- Changes:
- Verification:
- Notes:
