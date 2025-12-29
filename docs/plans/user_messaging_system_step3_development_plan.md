# User Messaging System – Step 3 Development Plan

1. **Stage 1 – Messaging database + models**
   - Goal: Introduce a dedicated SQLModel engine (e.g., `messaging_engine`) and define `MessageThread`, `MessageParticipant`, and `Message` models keyed to existing `User.id`.
   - Dependencies: `AI_PROJECT_GUIDE.md` modular module guidance; existing `app/db.py` for engine patterns.
   - Expected changes: Config hook for messaging DB path, engine/session helpers under a new `app/modules/messaging/db.py`, model definitions referencing user IDs and timestamps.
   - Verification: `python -m app.modules.messaging.tests` (or shell script) to instantiate the engine and create tables; manual check that the new DB file appears in `data/messages.db`.
   - Risks/open: Ensuring referential integrity without cross-database joins; deciding whether to mirror usernames for denormalized display.
   - Components/APIs touched: `app/config.py`, `app/db.py`, new module package.

2. **Stage 2 – Admin toggle + setup workflow**
   - Goal: Add an admin-controlled “Direct messaging” toggle exposed in existing settings UI/CLI.
   - Dependencies: Stage 1 (engine ready); `/admin/sync-control` or settings pages where toggles live.
   - Expected changes: Config flag (e.g., `ENABLE_MESSAGING`), persistence via existing settings table/service, CLI command to initialize messaging DB when toggled on.
   - Verification: Toggle on/off in admin UI, reload page to ensure state persists; CLI run logs confirming DB initialization only when enabling.
   - Risks/open: Deciding whether toggle lives in sync scope page or a new settings section; ensuring default off in all environments.
   - Components/APIs touched: `templates/admin/*.html`, admin settings routes/services, possibly `tools/dev.py`.

3. **Stage 3 – Profile entry points + nav affordances**
   - Goal: Surface “Message” buttons on profile/member views and an inbox badge/link in the global nav when messaging is enabled.
   - Dependencies: Stage 2 (need toggle to gate UI visibility).
   - Expected changes: Update `templates/profile/*.html`, `templates/base.html` nav partials, and corresponding FastAPI handlers to include messaging context in render data.
   - Verification: With toggle enabled, visit another member’s profile and confirm CTA renders; disable toggle and ensure UI disappears; check nav badge placeholder is hidden when zero unread.
   - Risks/open: Avoid exposing CTA when viewing own profile or unauthorized states; ensure SSR fallback works without JS.
   - Components/APIs touched: Profile routes/services, base layout, design tokens if new icons needed.

4. **Stage 4 – Conversation creation + send endpoints**
   - Goal: Implement FastAPI routes/forms to start a conversation and send initial messages, writing to the messaging DB while logging metadata in the primary DB for unread counts.
   - Dependencies: Stages 1–3 (models, toggle, UI entry points).
   - Expected changes: New router under `app/modules/messaging/routes.py`, service functions (`create_thread`, `send_message`), CSRF-protected forms or JSON endpoints, background task (if needed) to update unread metadata.
   - Verification: Manual flow starting a thread from a profile, confirming DB rows via CLI/SQLite browser, and verifying HTTP 4xx when messaging disabled or unauthorized.
   - Risks/open: Handling race conditions when both participants start threads simultaneously; ensuring message text never touches the primary DB.
   - Components/APIs touched: FastAPI routers, services, form templates, JSON API contract (documented for future automation).

5. **Stage 5 – Inbox + thread views**
   - Goal: Build inbox list and message thread pages integrated into existing dashboard layout.
   - Dependencies: Stage 4 (messages exist).
   - Expected changes: New templates for inbox and thread detail, list queries joining thread participants to user metadata (read-only cross-db via service layer), pagination helpers, reply form.
   - Verification: Send messages between two test accounts, confirm inbox shows threads sorted by latest activity, thread view loads messages chronologically, replies append instantly (SSR + optional fetch).
   - Risks/open: Avoid heavy N+1 lookups when enriching participant data; figure out retention/deletion controls for future stages.
   - Components/APIs touched: Dashboard route, new messaging templates, optional JS enhancement for auto-scroll.

6. **Stage 6 – Unread counts + notifications**
   - Goal: Track unread counts per participant and surface badges in nav/dashboard.
   - Dependencies: Stage 5 (UI surfaces), Stage 4 (message sends).
   - Expected changes: `MessageParticipant` fields for `last_read_at`, services to mark read on thread view, background update to set counts stored in main DB (or cached) for quick lookup, nav context update.
   - Verification: Trigger unread by sending message, validate badge increments, open thread to mark read, confirm badge clears without refresh glitches; add regression test for API responses.
   - Risks/open: Synchronizing counts between two databases; ensuring badge queries remain lightweight; handling concurrent reads on multiple devices.
   - Components/APIs touched: Messaging services, nav context provider, optional API endpoint for polling.

7. **Stage 7 – Ops instrumentation + docs**
   - Goal: Document backup/retention expectations and add basic telemetry for messaging usage.
   - Dependencies: Prior stages complete.
   - Expected changes: README/spec updates summarizing messaging behavior, CLI/admin docs for managing the messaging DB, metrics/log hooks (counts of messages sent, toggle state changes), and test plan addendum.
   - Verification: Docs reviewed, `./wb` help text shows new commands, log statements confirmed during local testing.
   - Risks/open: Ensuring documentation stays concise; providing clear guidance for future retention policies even if not implemented yet.
   - Components/APIs touched: `README.md`, `docs/spec.md`, `AI_PROJECT_GUIDE.md`, logging config.
