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
  - Extended the messaging models with `direct_key` + `unread_count`, and built a dedicated service layer that can create direct threads, append messages, and surface thread summaries.
  - Added `/messages/direct` and `/messages/{thread_id}/messages` endpoints (guarded by the feature toggle) plus a placeholder inbox route so the new nav link no longer 404s.
  - Wired a CLI-safe schema reset path by re-initializing `data/messages.db` through the new service helpers.
- Verification:
  - Rebuilt the messaging DB via `./wb messaging init-db`, then used a Python harness (`services.send_direct_message(1, 2, "Hello")`) to confirm messages write to the dedicated store and threads track participants.
- Notes:
  - Placeholder GET `/messages` simply returns a stub for now; Stage 5 swaps in the real inbox/thread templates.

## Stage 5 – Inbox + thread views
- Changes:
  - Replaced the placeholder inbox with `templates/messaging/inbox.html` + `thread.html`, listing every conversation via the new service summaries and rendering a simple, server-rendered thread view with a send form.
  - Added GET routes for `/messages`, `/messages/{thread_id}`, and `/messages/with/{username}` so members can jump straight into a conversation from the nav, profile CTA, or members directory.
  - Updated the profile + directory CTA buttons to post to `/messages/direct`, keeping graceful-degradation forms in place while data attributes remain for future JS.
- Verification:
  - Exercised the messaging service in a Python shell (creating direct messages, listing summaries, loading threads) to ensure the templates have data to render without errors.
- Notes:
  - Thread templates currently use simple stacked cards; Stage 6 will wire unread counts/badges in the nav and inbox cards.

## Stage 6 – Unread counts + notifications
- Changes:
  - Added a `messaging_unread_count()` helper so templates can ask for a user’s unread total, and updated the account nav/Inboxes to display live badges sourced from `MessageParticipant.unread_count`.
  - Wired the helper into the nav so fully authenticated members see their unread tally beside the Inbox link.
- Verification:
  - Toggled `ENABLE_DIRECT_MESSAGING` on in a Python shell, sent cross-user messages via the service, and confirmed `messaging_unread_count(1)` reflects the expected unread value while the sender’s count stays at zero.
- Notes:
  - Stage 7 will wrap up documentation and CLI guidance for backups/backfilling.

## Stage 7 – Ops instrumentation + docs
- Changes:
  - Documented the messaging toggle/CLI workflow in `README.md`, `AI_PROJECT_GUIDE.md`, and `docs/spec.md` so operators know to run `./wb messaging init-db` and where to find the Inbox routes.
  - Highlighted that the messaging database lives at `data/messages.db`, separate from `data/app.db`, to keep backup/retention plans isolated.
- Verification:
  - Manual doc review to ensure each reference clearly calls out the toggle location plus the CLI command required to initialize the dedicated store.
- Notes:
  - Future instrumentation (analytics, retention policies) can hook into the messaging service layer without touching the primary DB.
