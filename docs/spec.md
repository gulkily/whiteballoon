# WhiteBalloon Functional Specification

## Overview
WhiteBalloon is a modular FastAPI + SQLModel application that combines
invite-based authentication, a collaborative help-request feed with comment
threads, profile management, and admin-operated sync tooling. The user-facing
frontend is server-rendered with vanilla CSS and minimal progressive
enhancement so the project can be restored accurately using this document.

## Core Behaviors

### Authentication & Session Lifecycle
- Registrations are invite-only after the first account. The first user becomes
  an administrator automatically and is issued a fully authenticated session.
- Login is username-only. Submitting the form creates an
  `AuthenticationRequest`, a pending `UserSession`, and shows the verification
  code to the member.
- Entering the code (self-serve or via an admin) upgrades the existing session
  to `is_fully_authenticated=True`, promoting any pending requests created by
  that user.
- Sessions persist in the database and are referenced by the
  `wb_session_id` cookie. Sessions include timestamps for expiry and
  last-seen tracking.
- Registration optionally stores a contact email, links personalization data
  from the invite, and can submit an initial request that immediately lands in
  the pending queue.
- Session roles determine visible UI:
  - **Logged out** – landing and CTA pages rendered from
    `templates/auth/logged_out.html`.
  - **Half-authenticated** – read-only dashboard showing the active verification
    code, all open requests, and any requests the user posted while pending.
    Users can submit new requests, but they are stored with `status="pending"`
    until approval.
  - **Fully authenticated** – full dashboard with creation, completion, and
    comment capabilities.

### Requests & Comments
- The root (`/`) renders the request dashboard via `templates/requests/index.html`
  or `templates/requests/pending.html` depending on session status. Both pages
  load a collapsible request form enhanced by `static/js/request-feed.js`.
- Requests have `open`, `pending`, or `completed` status plus timestamps,
  creator metadata, contact email, and `sync_scope` (private/public).
- Half-authenticated submissions land in the `pending` bucket. Once the session
  is approved the backend promotes those records to `open`.
- Request details live at `/requests/{id}` and include a comment thread. Fully
  authenticated users can post comments via standard form POSTs or via fetch.
  Admins can soft-delete comments. Non-admin viewers cannot see pending
  requests that they did not create.
- Marking a request complete is available to admins or the requester. JS calls
  `POST /api/requests/{id}/complete`; the server-rendered fallback posts to
  `/requests/{id}/complete` and redirects.

### Progressive Enhancement
- Every screen renders fully via SSR. Enhancements include: toggling the
  request form, refreshing the feed after API mutations, and rendering newly
  posted comments without a full reload.
- Each interactive area provides a `<noscript>` fallback or a traditional form
  post so non-JS environments remain usable.

### Profiles, Invites, and Social Graph
- Invites are created from `/invite/new`. Admins/power users can upload a photo
  (stored under `static/uploads/invite_photos`), craft gratitude and support
  notes, suggest usernames/bios, and optionally mark the invite as
  publicly-shareable (sets `sync_scope="public"`).
- Invite tokens enforce `max_uses`, optional expiry, auto-approval, and track
  personalization in `InvitePersonalization` rows. Registration reads the
  invite to prefill copy and avatar suggestions.
- Members manage contact email and avatar from `/settings/account`. Avatars are
  stored through `user_attribute_service` and surfaced in nav bars.
- `/profile` summarizes the signed-in member’s privileges. `/people/{username}`
  renders another member’s profile, redacting contact info unless the viewer is
  an admin or the same user.
- `/invite/map` visualizes the bidirectional invite graph, caching results per
  user in `InviteMapCache`.

### Administration & Sync
- `/admin` hosts quick links for administrators. `/admin/profiles` provides a
  paginated, filterable directory of every local account, with drill-down views
  showing their requests, invites, and metadata.
- `/admin/dedalus` controls the optional Dedalus API key that powers the Mutual
  Aid Copilot integration. Keys are stored in `.env` with verification history.
- `/admin/sync-control` exposes peer management for the Git-style sync system:
  admins can add/edit/delete peers, queue push/pull jobs, and view job history.
- `/sync/scope` lets admins toggle the public/private state of requests,
  comments, users, and invites. `/sync/public` summarizes what will be exported
  (bundle manifest, signature verification, and stored public keys).
- The developer-operated sync hub runs via `wb hub serve`, reusing the same
  keypairs and bundle verification utilities.

## API Endpoints

### Auth
- `POST /auth/register` – create a user, optionally saving contact email and an
  initial request. Responds with metadata about auto-approval.
- `POST /auth/login` – request access for an existing username. Returns the
  `auth_request_id`, current status, and verification code.
- `POST /auth/login/verify` – confirm the pending request with a verification
  code, promoting the linked session.
- `POST /auth/logout` – revoke the current session, clear the cookie.
- `POST /auth/invites` – admin/session-user form that creates an invite token
  with personalization metadata and photo upload.
- `GET /auth/requests/{auth_request_id}` – admin endpoint returning status and
  approval info for a specific auth request.

### Requests API
- `GET /api/requests` – JSON list of non-pending requests, enriched with
  creator usernames, timestamps (ISO 8601 + `Z`), contact email, `can_complete`,
  and `sync_scope`.
- `GET /api/requests/pending` – JSON list of pending requests created by the
  current session user.
- `POST /api/requests` – create a new request (`description`, optional
  `contact_email`). Automatically sets status to `open` or `pending` based on
  session.
- `POST /api/requests/{id}/complete` – mark a request as completed and return
  the updated record without the completion action.

### HTML form endpoints
- `POST /requests` – server-rendered request creation (non-JS fallback).
- `POST /requests/{id}/complete` – fallback for marking completion.
- `POST /requests/{id}/comments` – create a comment (requires fully
  authenticated session). Supports JSON responses when `Accept: application/json`.
- `POST /requests/{id}/comments/{comment_id}/delete` – admin-only soft delete of
  comments.

## Frontend Structure
- `templates/base.html` – root layout loading the design system CSS and the
  request-feed enhancement script.
- `templates/auth/*.html` – login, pending verification, register, and
  invite-required flows.
- `templates/requests/index.html` / `pending.html` – dashboards for fully and
  half-authenticated sessions. Include partials under
  `templates/requests/partials/` for list items and comments.
- `templates/requests/detail.html` – single-request page with comment thread
  and moderation controls.
- `templates/invite/new.html` and `templates/invite/map.html` – invite creation
  workflow and graph visualization.
- `templates/profile/*.html` – user profile and directory views.
- `templates/settings/account.html` – account settings and avatar management.
- `templates/admin/*.html` – admin panel, profile directory, Dedalus settings.
- `templates/sync/*.html` – sync control center and public bundle review.
- `static/js/request-feed.js` – progressive enhancement for the request form
  and completion actions.
- `static/css/app.css` – design system and helpers like `.is-collapsed`/
  `.is-expanded` used by the feed cards.

## CLI & Tooling
- `./wb` bootstraps a virtual environment (via `wb setup`), installs
  dependencies, and delegates to `tools/dev.py`.
- Core commands:
  - `wb runserver [--host --port --reload]` – start the FastAPI app with
    uvicorn (preflight ensures port availability).
  - `wb init-db` – create or migrate the SQLite database without dropping data.
  - `wb create-admin <username>` – promote a user to admin.
  - `wb create-invite [--username --max-uses --expires-in-days --no-auto-approve]`
    – issue invite tokens from the CLI.
  - `wb session list|approve|deny` – inspect and manage authentication requests.
  - `wb sync ...` – export/import bundles, push/pull peers, manage peer entries,
    and generate/verify signing keys.
  - `wb skins build|watch` – compile and watch optional skin bundles.
  - `wb hub serve|admin-token` – run the sync hub or create hashed admin tokens.
  - `wb update-env` – sync `.env` with `.env.example` defaults.
- `docs/plans/` and related documents contain the planning artifacts referenced
  during feature development and should be consulted when extending modules.

## Documentation Maintenance
- Update `docs/spec.md` whenever functional changes land so this document stays
  authoritative for new developers.
- Keep the SSR + progressive enhancement philosophy front-and-center, and add
  new modules or flows to the appropriate sections above.
