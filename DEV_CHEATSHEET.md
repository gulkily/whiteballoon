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

# Environment Configuration
cp .env.example .env                # Copy defaults and adjust as needed
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

## Environment Variables
```bash
DATABASE_URL=sqlite:///data/app.db
SECRET_KEY=changeme
SESSION_EXPIRY_MINUTES=20160        # 14 days
COOKIE_SECURE=false                 # Set true in production

# Optional features
ENABLE_CONTACT_EMAIL=true           # Allow users to store a contact email
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
- Run `pytest --maxfail=1` during development for quick feedback
- Document any new CLI commands or module hooks as they are added
