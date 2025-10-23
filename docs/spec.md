# WhiteBalloon Functional Specification

## Overview
WhiteBalloon is a modular FastAPI + SQLModel application providing invite-based authentication and a request feed. The frontend is server-rendered with vanilla CSS and minimal progressive enhancement. Documentation is kept current so the project can be rebuilt accurately from scratch using this specification.

## Core Behaviors

### Authentication & Sessions
- Invite-only registration; the first user becomes admin automatically.
- Login requires username; creates a pending authentication request and half-authenticated session.
- Verification via code upgrades the session to fully authenticated.
- Sessions stored in the database; cookies (`wb_session_id`) track the active session.
- Registration optionally captures contact email and initial request.

### Request Feed
- Authenticated users see a server-rendered request list on `/`.
- Request form is collapsed by default; a button reveals it using vanilla JS.
- Submitting a request uses `POST /api/requests`; JS refreshes the list; form resets and collapses.
- Completing a request issues `POST /api/requests/{id}/complete`; JS refreshes list, preserving server-rendered fallback (non-JS redirects via `/requests` form).
- Request records include description, optional contact email, status, timestamps.

### Progressive Enhancement
- Initial pages render fully with required data (SSR). JavaScript enhances interactions (form toggle, fetch updates).
- Without JS, forms submit normally (full reload). `<noscript>` provides alternative forms where needed.

### Session States & UI
- **Logged out**: shows welcome page with sign-in/invite CTAs.
- **Half-authenticated (awaiting approval)**: user can browse the feed in read-only mode, prepare request drafts client-side, and sees their verification code with an explicit message that changes remain private until approval. Submissions are blocked from persisting on the server.
- **Fully authenticated**: full request dashboard with create/complete actions stored server-side.

## API Endpoints
- `POST /auth/register` – create user, optional initial request.
- `POST /auth/login` – request access; responds with verification page.
- `POST /auth/login/verify` – approve request via code.
- `POST /auth/logout` – delete session cookie.
- `POST /api/requests` – create request (JSON body: `description`, optional `contact_email`).
- `POST /api/requests/{id}/complete` – mark request completed.
- `GET /api/requests` – JSON list of requests (description, status, timestamps, contact).

## Frontend Structure
- `templates/base.html` – shared layout, loads CSS and progressive enhancement script.
- `templates/auth/login.html` & `login_pending.html` – SSR forms with inline error display.
- `templates/requests/index.html` – server-rendered list with collapsible form.
- `static/js/request-feed.js` – handles form toggle and fetch interactions; expects SSR markup classes.
- `static/css/app.css` – design system; includes `.is-collapsed`/`.is-expanded` behavior.

## CLI & Tooling
- `./wb` wrapper invokes Click CLI (`tools/dev.py`) with commands `runserver`, `init-db`, `create-admin`, `create-invite`.
- `docs/plans/` contains planning artifacts per feature process.

## Documentation Maintenance
- Update `docs/spec.md` after functional changes to keep this spec authoritative.
- Reflect SSR+progressive philosophy and any new modules or flows in this document.
