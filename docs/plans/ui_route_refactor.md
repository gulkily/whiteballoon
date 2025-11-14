# UI Route Refactor Plan

## Overview
`app/routes/ui.py` has grown to ~1.4k lines and now mixes landing pages, invite flows, profile pages, sync admin tools, etc. To keep the codebase manageable, we will break the routes into focused modules (one per concern) and aggregate them via a lightweight package. This document outlines the structure and migration plan.

## Target Layout
```
app/routes/
  __init__.py          # Registers subrouters with the FastAPI app
  auth.py              # Existing auth API endpoints (unchanged for now)
  ui/
    __init__.py        # Imports and includes UI routers
    home.py            # Landing feed, public pages
    invites.py         # Invite creation + views
    requests.py        # Help-request CRUD & comments
    sync.py            # Sync control center and jobs
    profile.py         # Profile views + contact controls
    settings.py        # Account/settings pages
    sessions.py        # Login/logout/pending steps
    misc.py            # Any small leftover routes (or split further as needed)
```

Each module defines its own `router = APIRouter(...)` (with optional prefix/tags) and exposes it via `__all__`. Shared utilities (template helpers, formatting) go into a non-router helper module (`app/routes/ui/helpers.py`) to avoid circular imports.

## Step-by-Step Migration
1. **Scaffold package**
   - Create `app/routes/ui/__init__.py` and stub modules listed above.
   - Update `app/main.py` to import routers from `app.routes.ui` instead of `app.routes.ui:router`.

2. **Move routes incrementally**
   - Start with a small, self-contained section (e.g., sync control pages). Move relevant handlers + helper functions into `sync.py`, keeping the same FastAPI `@router.get/post` decorators and dependencies.
   - After each move, run targeted tests (e.g., `pytest tests/routes/test_sync_admin.py`) and manual browser checks for affected pages.
   - Repeat for the next logical group (invites, profiles, settings, requests, etc.), aiming for 150–200 lines per commit to keep diffs reviewable.

3. **Normalize helpers**
   - If multiple modules use the same helper, relocate it to `app/routes/ui/helpers.py` (or reuse existing services/dependencies) and import from there.

4. **Adjust imports/tests**
   - Update any direct imports from `app.routes.ui` in tests or other modules to point to the new files.
   - Because route paths remain unchanged, most tests should continue to pass without modification besides import paths.

5. **Clean up and document**
   - Once `ui.py` is empty, remove it.
   - Update developer docs (e.g., `DEV_CHEATSHEET.md`, module READMEs) to describe the new layout and remind contributors to add new routes to the appropriate module.
   - Optionally add an ADR or changelog entry summarizing the structural refactor.

## Risks & Mitigations
- **Large diffs / regressions**: move one route group per commit and test immediately.
- **Shared state collisions**: consolidate shared helpers in a dedicated module to avoid circular imports.
- **Documentation drift**: update docs as part of the same change-set to avoid confusion.

## Definition of Done
- No routes remain in `app/routes/ui.py` (file removed).
- Each major UI concern lives in its own module with a clear router.
- Tests and linting pass after each move.
- Documentation reflects the modular structure.
