# WhiteBalloon

**WhiteBalloon** is a socially-authenticated mutual aid network built on an **open, transparent social graph** where every connection and interaction is publicly inspectable but personally private. Identities are represented by **disposable private keys** that are socially cross-authenticated — your inviter cryptographically vouches for you, forming a chain of verified trust rather than a database of static profiles. The result is a decentralized web of relationships where authenticity is earned, not claimed.

At its core, WhiteBalloon is a **trust-driven coordination engine**: an invite-only network where every participant begins by expressing a real need and where visibility, recommendations, and introductions are shaped by degrees of separation. The **AI layer** continuously reads the open graph to suggest helpers, draft introductions, and surface mutual aid opportunities across clusters of trust. The infrastructure — built on FastAPI, SQLModel, and open cryptographic primitives — is deliberately minimal, designed to make social cooperation computationally legible without centralizing control. By merging open data, social verification, and AI mediation, WhiteBalloon reimagines the social network as an *infrastructure of care and reciprocity*, not performance.

# Technical Info

WhiteBalloon is a modular FastAPI + SQLModel application that ships with invite-only authentication and a lightweight help-request feed. The project serves as a foundation for layering additional atomic modules without adopting heavy frontend frameworks.

## Features
- Invite-based registration with automatic admin bootstrap for the first user
- Auto-approval for invite-based registrations (configurable per invite), allowing trusted users to land in a fully authenticated session immediately
- Multi-device login approvals powered by verification codes
- Session management via secure cookies backed by the database
- Help-request feed with progressive enhancement for creating and completing requests
- Vanilla CSS design system with reusable layout primitives and components
- JSON API under `/api/requests` for programmatic access to the request feed
- Invite generation returns share-ready links using the current request origin (fallback to `SITE_URL`)
- Animated, bubbly theme with gradient background/responsive cards inspired by mutual-aid celebrations (respects `prefers-reduced-motion`)

## Quick start

Requires Python 3.10+.

1. **Setup the environment** (creates venv, installs deps, initializes database)
   ```bash
   ./wb setup
   ```
   On Windows:
   ```cmd
   wb.bat setup
   ```

2. **Run the development server**
   ```bash
   ./wb runserver
   ```
   On Windows:
   ```cmd
   wb.bat runserver
   ```
   Visit `http://127.0.0.1:8000` to access the interface.

> **Note**: The first registered user (no invite token required) becomes an administrator automatically.

> **Database integrity**: Re-run `./wb init-db` whenever you suspect schema drift. The command now checks tables/columns against SQLModel definitions, auto-creates missing pieces, and reports mismatches that require manual attention.

> **Invite links**: By default invite links use the incoming request origin. Set `SITE_URL` in `.env` to provide a fallback host for CLI usage or non-HTTP contexts.

## Send Welcome page
- While signed in, use the “Send Welcome” button (header menu) to generate an invite instantly.
- The page shows the invite link, token, QR code, and optional fields for suggested username/bio to share with the invitee.
- Shared links pre-fill the token when invitees visit `/register`.

## Authentication workflow
1. A user registers with an invite token (unless they are the first user).
2. If the invite was issued by an approved admin (auto-approve default), the user is fully authenticated instantly and receives a logged-in session.
   Otherwise, the user submits their username on the login page, creating an authentication request and half-authenticated session.
3. While waiting, the user lands on a pending dashboard: they can browse existing requests, save private drafts, and view their verification code.
4. The user (or an administrator) completes verification by submitting the generated code, upgrading the session to fully authenticated.
5. Sessions are stored in the database and tracked through the `wb_session_id` cookie.

The CLI exposes helpers for administration:
```bash
./wb create-admin <username>
./wb create-invite --username <admin> --max-uses 3 --expires-in-days 7
./wb session list                              # Inspect pending authentication requests
./wb session approve <request_id>             # Approve a request from the CLI
./wb session deny <request_id>                # Deny a pending request
```

## Request feed basics
- Lightweight JavaScript helpers drive optional in-place updates; initial pages remain server-rendered.
- The feed page loads from `/` and the backing API lives under `/api/requests`.
- Authenticated users can post new requests, optionally sharing a contact email for follow-up.
- Half-authenticated users can submit requests which remain private (`pending` status) until approval.
- Authors and administrators can mark requests as completed; the UI reflects updates instantly.

## Project layout
```
app/
  config.py             # Environment and settings helpers
  db.py                 # Engine factory and session dependency
  dependencies.py       # FastAPI dependency utilities
  main.py               # App factory and router registration
  models.py             # SQLModel tables (users, sessions, requests, invites)
  modules/              # Pluggable feature modules (requests feed)
  routes/               # API + UI routers
  services/             # Domain services (authentication helpers)
static/css/app.css      # Vanilla CSS design system
templates/              # Jinja templates and enhancement-friendly partials
tools/dev.py            # Click CLI (invoked via wb/wb.bat)
wb.py                   # Cross-platform Python launcher
wb / wb.bat             # Thin wrappers for Linux/macOS and Windows
```

## Adding new modules
1. Create a package under `app/modules/<module_name>/` with `services.py` and optional routers.
2. Register the module in `app/modules/__init__.py` so `register_modules()` wires it into the app.
3. Provide templates and static assets under `templates/<module_name>/` and `static/` as needed.
4. Document the feature using the four-step planning process in `docs/plans/`.
5. Add CLI helpers or UI routes when the module requires interactive workflows.

## Deployment notes
- Static assets are served directly by FastAPI; for production behind a proxy, ensure `/static` is cached appropriately.
- Migrate from SQLite to another database by adjusting `DATABASE_URL` in `.env` and ensuring the driver is installed.
- Set `COOKIE_SECURE=true` and supply a strong `SECRET_KEY` before running in production.
