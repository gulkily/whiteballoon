# WhiteBalloon

WhiteBalloon is a modular FastAPI + SQLModel application that ships with invite-only authentication and a lightweight help-request feed. The project serves as a foundation for layering additional atomic modules without adopting heavy frontend frameworks.

## Features
- Invite-based registration with automatic admin bootstrap for the first user
- Multi-device login approvals powered by verification codes
- Session management via secure cookies backed by the database
- Help-request feed with progressive enhancement for creating and completing requests
- Vanilla CSS design system with reusable layout primitives and components
- JSON API under `/api/requests` for programmatic access to the request feed

## Quick start
1. **Bootstrap the environment**
   ```bash
   ./wb setup
   ```
2. **Initialize the database**
   ```bash
   ./wb init-db
   ```
3. **Run the development server**
   ```bash
   ./wb runserver
   ```
   Visit `http://127.0.0.1:8000` to access the interface.

> **Note**: The first registered user (no invite token required) becomes an administrator automatically.

## Authentication workflow
1. A user registers with an invite token (unless they are the first user).
2. The user submits their username on the login page, creating an authentication request and half-authenticated session.
3. While waiting, the user lands on a pending dashboard: they can browse existing requests, save private drafts, and view their verification code.
4. The user (or an administrator) completes verification by submitting the generated code, upgrading the session to fully authenticated.
5. Sessions are stored in the database and tracked through the `wb_session_id` cookie.

The CLI exposes helpers for administration:
```bash
./wb create-admin <username>
./wb create-invite --username <admin> --max-uses 3 --expires-in-days 7
```

## Request feed basics
- Lightweight JavaScript helpers drive optional in-place updates; initial pages remain server-rendered.
- The feed page loads from `/` and the backing API lives under `/api/requests`.
- Authenticated users can post new requests, optionally sharing a contact email for follow-up.
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
tools/dev.py            # Typer CLI (invoked via ./wb)
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
