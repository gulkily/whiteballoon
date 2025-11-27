# WhiteBalloon - Development Cheatsheet

## Project Snapshot
Modular FastAPI/SQLModel application with authentication, request feed, server-rendered templates, and progressive enhancement via light JavaScript helpers. Future capabilities will be delivered as atomic modules packaged under `app/modules/`.

## Quick Start Commands
```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Development
./wb init-db               # Initialize the SQLite database
./wb runserver                # Start development server (wraps uvicorn)
./wb create-admin USER        # Promote an existing user to administrator
./wb create-invite [options]  # Generate invite tokens (admin required)
./wb session list             # View authentication requests (pending by default)
./wb session approve ID       # Approve request and promote pending content
./wb session deny ID          # Deny request and invalidate sessions

# Environment Configuration
cp .env.example .env                # Copy defaults and adjust as needed
# CSS skins
./wb skins build               # Rebuild hashed bundles after editing static/skins
./wb skins watch               # Rebuild on change during frontend work
```

## Feature Development Process
For every new feature or module, follow the four-step process in `FEATURE_DEVELOPMENT_PROCESS.md`:
1. **Solution Assessment** (optional) – Compare approaches when direction is unclear.
2. **Feature Description** – Define problem, user stories, core requirements, flow, success criteria.
3. **Development Plan** – Break work into atomic stages (<2 hours), outline testing and risks.
4. **Implementation** – Create a feature branch, ship each stage with tests, and document the outcome.

## Core Architecture Reminders
- `app/main.py` – App factory, middleware, and router registration
- `app/models.py` – SQLModel definitions (`User`, `Session`, `HelpRequest`, and future module models)
- `app/services/` – Shared domain services (invites, sessions, request feed)
- `app/routes/` – API + UI routers
- `app/modules/` – Optional feature modules loaded via plug-in registration
- `templates/` – Jinja templates shared by modules
- `static/css/app.css` – Vanilla CSS design system for layout/components
- `wb` – Git-style wrapper around the Click CLI
- `static/js/` (optional) – Minimal progressive-enhancement scripts

## Templating Guidelines
- Keep all HTML markup (pages, fragments, styled blocks) inside Jinja templates under `templates/`.
- When a Python handler needs to return HTML, render a template via `Jinja2Templates` instead of building strings inline.
- If you introduce new views (CLI output, hub pages, etc.), create the template at the same time so we never accumulate inline HTML debt again.
- **Dynamic updates**: When a page needs partial refreshes, use vanilla JavaScript (`fetch`) to call dedicated endpoints that return HTML or JSON snippets (see `static/js/comment-insights.js` for the pattern). Do not add HTMX/Stimulus or other frontend dependencies.

## Environment Variables
```bash
DATABASE_URL=sqlite:///data/app.db
SECRET_KEY=changeme
SESSION_EXPIRY_MINUTES=20160        # 14 days
COOKIE_SECURE=false                 # Set true in production

# Optional features
ENABLE_CONTACT_EMAIL=true           # Allow users to store a contact email
COMMENT_INSIGHTS_INDICATOR=false    # Show LLM insight badges inline (admin-only, default off)
```

## Module Playbook (High-Level)
When creating a new module:
- Scaffold under `app/modules/<module_name>/` with `routes.py`, `services.py`, optional `models.py`
- Register router in `app/main.py` with a lightweight include helper
- Add templates to `templates/<module_name>/` and static assets under `static/`
- Document module-specific settings and plan stages in `docs/plans/`
- Provide tests under `tests/modules/<module_name>/`

## Tooling Tips
- Keep dependencies minimal; prefer standard library or existing packages
- Do **not** run `pytest` during development; rely on targeted manual checks instead
- Document any new CLI commands or module hooks as they are added

## Database integrity
- `./wb init-db` now verifies existing tables/columns against SQLModel metadata, recreates missing pieces where safe, and warns about mismatches. Run it whenever you pull structural changes or suspect schema drift.

## Invite links
- `./wb create-invite` prints a shareable `/register` link using `SITE_URL` as a fallback base. Set `SITE_URL` in `.env` for non-local environments to ensure links point to the correct host.
- The in-app “Send Welcome” page (`/invite/new`) generates invites with link + QR and optional invitee details; ensure appropriate permissions before exposing it.

## Ctrl-C handling pattern
- Use `wb.py`'s `_run_process([...], graceful_interrupt=True, interrupt_message="...")` helper when spawning subprocesses that should stop cleanly on `Ctrl-C`. It forwards SIGINT to the child, suppresses stack traces, and prints the optional friendly message (see `cmd_known` / `runserver`).
- For interactive terminal work (raw input, REPLs), wrap the invocation with `_suppress_ctrl_c_echo(True)` so the terminal does not echo `^C` characters while still letting the parent handle interrupts later.
- When writing a pure-Python loop (no subprocess), wrap the body in `try: ... except KeyboardInterrupt: log("<message>"); return 0` so we always exit gracefully.
- Always log a short status update (e.g., "Server stopped" or "Dedalus verification stopped") after cancelling work so callers know the shutdown was intentional.
