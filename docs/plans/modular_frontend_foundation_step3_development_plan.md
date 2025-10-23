# Modular Frontend Foundation – Development Plan

- **Bootstrap Prompt**:
  ```
  You are starting from an empty folder to create a fresh project that delivers secure authentication and a minimal request feed, while establishing a foundation for future plug-in modules. Build a FastAPI + SQLModel backend with the following structure:
  - Project layout: `app/` (FastAPI app package), `app/services/`, `app/routes/`, `app/modules/`, `app/models.py`, `templates/`, `static/css/`, `tests/`, `tools/`.
  - Features: invite-based authentication flow, session tokens stored in DB, optional contact email capture on profile, CRUD endpoints and progressively enhanced templates for a "help requests" feed (list, create, mark complete).
  - Dependencies: FastAPI, SQLModel, Jinja2, passlib[bcrypt], python-multipart, httpx (for tests), pytest, pytest-asyncio, uvicorn.
  - Database: SQLite `data/app.db` with SQLModel models for `User`, `Session`, `HelpRequest` (includes `title`, `description`, `created_at`, `status`, `contact_email` optional).
  - Authentication: invite-only registration, multi-device login approvals, logout, session cookie, admin flag to gate future features.
  - Frontend: Jinja base template with custom vanilla CSS variables, layout primitives, and lightweight progressive enhancement. No Tailwind or external CSS frameworks; ship plain CSS in `static/css/app.css` without build tooling.
  - CLI: `tools/dev.py` (Typer) with commands `runserver`, `init-db`, `create-admin`.
  - Tests: pytest suite covering auth flow and help request CRUD (async client via httpx AsyncClient + LifespanManager).
  - Docs: `README.md` with setup, CSS guidelines, architecture overview, and notes on how additional modules can hook into the project.
  Ensure lint-friendly code, type hints, and keep stages <2 hours each.
  ```

1. **Stage 1 – Repository Bootstrap & Tooling**
   - Dependencies: Bootstrap prompt above; Python 3.10+ environment.
   - Changes: Initialize project skeleton, configure dependency management, add `.env.example`, scaffold `tools/dev.py` with Typer app placeholder.
   - Risks: Environment mismatch; mitigate with clear setup docs.

2. **Stage 2 – Data Models & Persistence Layer**
   - Dependencies: Stage 1 structure in place.
   - Changes: Implement SQLModel models (`User`, `Session`, `HelpRequest`), database engine helpers, session dependency, and CLI `init-db` command.
   - Risks: Schema drift when adding future modules; mitigate by documenting extension points and using migrations only when unavoidable.

3. **Stage 3 – Authentication & Session Services**
   - Dependencies: Stage 2 models available.
   - Changes: Build invite consumption, username-based login that creates approval requests, session lifecycle utilities, and admin flag handling.
   - Risks: Authentication regressions; mitigate with careful approval flow checks and session expiry defaults.

4. **Stage 4 – Request Feed Module (Core Module 1)**
   - Dependencies: Stage 3 authentication available.
   - Changes: Implement module scaffold under `app/modules/requests/` with routes, services, templates, and progressive enhancement hooks for listing, creating, and completing requests.
   - Risks: Module coupling; mitigate by encapsulating business logic in module service layer and exposing clean interfaces.

5. **Stage 5 – Frontend Templates & Custom CSS System**
   - Dependencies: Stages 3–4 endpoints stable.
   - Changes: Implement `templates/base.html`, auth views, shared partials, and `static/css/app.css` with tokens, layout utilities, and components used by modules.
   - Risks: Style drift across modules; mitigate with documented design tokens and component guidelines.

6. **Stage 6 – Documentation, QA, and Module Playbook**
   - Dependencies: All prior stages complete.
   - Changes: Write README with setup instructions, CSS guidelines, module playbook, and CLI usage; add docs explaining how to create new modules; ensure CLI commands work end-to-end.
   - Risks: Documentation drift; mitigate with final checklist and plan for future module docs.

7. **Stage 7 – Future Module Scaffold (Optional)**
   - Dependencies: Stage 6 complete.
   - Changes: Provide template project files or cookiecutter snippet for new modules (e.g., README snippet, test skeleton), ensuring the system is ready to host additional atomic modules.
   - Risks: Over-engineering; keep optional and light-weight.
