# WhiteBalloon - Project Guide

## Environment Context
- All development happens in the local environment contained in this repository
- Do not attempt to diagnose or change production systems directly from this workspace
- Avoid `sudo` and global package installs; rely on project tooling instead
- Use the Typer CLI we ship in `tools/dev.py` to run local workflows (server, database init, admin creation)

## Project Overview
WhiteBalloon is a modular community platform built on FastAPI and SQLModel. The initial milestone focuses on foundational authentication and a feed of user-submitted requests. Over time we will layer in additional atomic modules (e.g., announcements, lightweight CRM, analytics) that plug into the same scaffolding without rewriting the core stack.

## Technology Stack
- **Backend**: FastAPI application packaged under `app/`
- **Database**: SQLite with SQLModel ORM, stored at `data/app.db`
- **Frontend**: Jinja2 templates rendered by FastAPI with vanilla CSS and HTMX enhancements
- **Authentication**: Password-based registration/login backed by hashed credentials and session tokens stored in the database
- **CLI Tooling**: Typer-based developer commands in `tools/dev.py`
- **Testing**: Pytest with `httpx.AsyncClient` + FastAPI Lifespan Manager for end-to-end coverage

## Modular Architecture Vision
The platform is designed so that new capabilities can be added as _atomic modules_. Each module should:
- Declare its routes, templates, and static assets within a dedicated package under `app/modules/<module_name>/`
- Expose a small service layer for business logic that the rest of the app can call
- Register dependencies and background tasks without tightly coupling to other modules
- Provide its own plan documents (`docs/plans/<module_name>_*.md`) that follow the feature process below

The base authentication and request feed modules serve as reference implementations for this pattern. Future modules should follow the same structure to keep onboarding and maintenance predictable.

## Repository Layout (Target)
- `app/main.py` – FastAPI app factory and router registration
- `app/models.py` – SQLModel models for `User`, `Session`, and `HelpRequest`
- `app/services/` – Authentication, session, and request feed services
- `app/routes/` – APIRouter definitions for auth and request management
- `app/modules/` – Optional directory for plug-in modules packaged independently
- `templates/` – Jinja2 templates (base layout, auth pages, request feed views, HTMX fragments)
- `static/css/app.css` – Custom vanilla CSS design system (no external frameworks)
- `data/` – SQLite database files and derived artifacts
- `tests/` – Pytest suite for unit, integration, and functional coverage
- `tools/dev.py` – Typer CLI for `runserver`, `init-db`, `create-admin`, and future utilities
- `docs/plans/` – Planning documents for each feature/module stage

## Core Features (Milestone 1)
1. User registration, login, logout, and session management
2. Optional profile contact email capture for follow-up
3. Request feed that lists, creates, and completes user-submitted requests
4. HTMX-powered interactions for in-place request creation/completion
5. Vanilla CSS design system with tokens, layout primitives, and component patterns

## Extensibility Guidelines
- Each module should ship with its own tests and documentation
- Favor configuration-driven behavior over schema changes whenever possible
- Use SQLModel relationships and services to encapsulate database logic per module
- Keep modules independent by communicating through service interfaces or event hooks
- Document module boundaries and dependencies in their respective plan files

## Feature Development Process
Follow the four-step process documented in `FEATURE_DEVELOPMENT_PROCESS.md`:
1. **Solution Assessment (Optional)** – Evaluate options when direction is unclear
2. **Feature Description** – Define problem, user stories, core requirements, and success criteria
3. **Development Plan** – Break work into atomic stages (<2 hours), outline testing and risks
4. **Implementation** – Create a feature branch, execute stages in order, run tests, and document the outcome

## Testing Strategy
- Keep fast unit tests near related modules (e.g., `tests/modules/<module_name>/test_services.py`)
- Use async integration tests to cover authentication flows and request feed endpoints
- Add frontend smoke tests to ensure templates render required placeholders
- When adding modules, include regression tests that exercise module boundaries

## Deployment Notes
- Local development: `uvicorn app.main:app --reload`
- Production deployment can layer in Gunicorn/Uvicorn workers once the CLI exposes appropriate commands
- Persist the SQLite database in `data/` or migrate to an external database by swapping the engine configuration in `app/db.py`

## Additional Resources
- `README.md` – Setup instructions and project overview (to be written during implementation)
- `README_PROMPT.md` – Bootstrap prompt for generating the initial codebase
- `docs/plans/` – Authoritative source for all feature planning artifacts
