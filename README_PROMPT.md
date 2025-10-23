# Project Bootstrap Prompt

You are starting from an empty repository. Follow the planning documents in `docs/plans/` to build a modular FastAPI + SQLModel application that ships foundational authentication and a request feed, while leaving room for future plug-in modules.

Use this prompt to kick off implementation:

```
You are starting from an empty folder to create a fresh project that delivers secure authentication and a minimal request feed, while establishing a foundation for future plug-in modules. Build a FastAPI + SQLModel backend with the following structure:
- Project layout: `app/` (FastAPI app package), `app/services/`, `app/routes/`, `app/modules/`, `app/models.py`, `templates/`, `static/css/`, `tests/`, `tools/`.
- Features: invite-based user onboarding with username authentication, session tokens stored in DB, optional contact email capture on profile, CRUD endpoints and progressively enhanced templates for a "help requests" feed (list, create, mark complete).
- Dependencies: FastAPI, SQLModel, Jinja2, passlib[bcrypt], python-multipart, httpx (for tests), pytest, pytest-asyncio, uvicorn.
- Database: SQLite `data/app.db` with SQLModel models for `User`, `Session`, `HelpRequest` (includes `title`, `description`, `created_at`, `status`, `contact_email` optional).
- Authentication: invite-only registration, multi-device login approvals, logout, session cookie, and an admin flag to gate future features.
- Frontend: Jinja base template with custom vanilla CSS variables, layout primitives, and lightweight progressive enhancement (vanilla JS). No Tailwind or external CSS frameworks; ship plain CSS in `static/css/app.css` without build tooling.
- CLI: `tools/dev.py` (Typer) with commands `runserver`, `init-db`, `create-admin`.
- Tests: pytest suite covering auth flow and help request CRUD (async client via httpx AsyncClient + LifespanManager).
- Docs: `README.md` with setup, CSS guidelines, architecture overview, and notes on how additional modules can hook into the project.
Ensure lint-friendly code, type hints, and keep stages <2 hours each.
```

Run that prompt from the repo root when you're ready to start implementation.
