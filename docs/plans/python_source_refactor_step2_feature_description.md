# Step 2 – Feature Description: Python Source Refactor

## Problem
The largest Python modules (notably `app/routes/ui/__init__.py` at 3,182 LOC) slow feature delivery because contributors must scroll through sprawling files, struggle to untangle dependencies, and risk merge conflicts on every change. We need a structure where cohesive features live in discrete modules without rewriting the routing stack.

## User Stories
- As a feature developer, I want to work inside focused files per surface so that I can implement or review changes without sifting through thousands of unrelated lines.
- As a reviewer, I want route and helper modules grouped by concern so that diffs isolate relevant logic and reduce review fatigue.
- As a QA engineer, I want the refactor to keep FastAPI registrations stable so that existing automated and manual tests continue to run without broad rework.

## Core Requirements
- Preserve current behavior: no endpoint paths, dependencies, or template wiring may change as part of the split.
- Introduce new modules/packages that encapsulate cohesive feature areas (e.g., auth routes, admin routes) with clear public entry points.
- Maintain import semantics so that other modules (tests, CLI tools) can resolve helpers without circular dependencies.
- Add guard documentation (README or module docstring) that explains the new structure for future contributors.
- Ensure lint/tests pass after each extraction to prove refactors are behavior-neutral.

## Shared Component Inventory
- **FastAPI app + routers (`app/routes/ui/__init__.py`, `app/routes/ui/admin.py`, `app/routes/ui/sync.py`)**: we will extend the existing `APIRouter` registrations, reusing the same helper functions, but relocate logic into submodules (e.g., `app/routes/ui/auth/handlers.py`). No new routing framework is introduced.
- **Templates referenced by the routes**: continue to reuse current Jinja templates (`templates/…`) with identical context data; only the Python composition moves.
- **Helper utilities (`app/routes/ui/helpers.py`, `app/tools/*`)**: shared helpers stay in existing modules initially, then can be split separately when their call sites shrink.

## Simple User Flow
1. Developer chooses a cohesive section (e.g., authentication routes) and creates a dedicated module/package for it.
2. Move the relevant route functions and related helpers into the new module, updating imports while keeping router registration code untouched.
3. Run lint/tests (and smoke FastAPI startup) to verify no regressions.
4. Repeat for the next section until no single module exceeds the agreed target size.

## Success Criteria
- Reduce each of the current top-three Python files (`app/routes/ui/__init__.py`, `app/routes/ui/admin.py`, `app/tools/comment_llm_processing.py`) below 800 LOC without changing external behavior.
- All automated tests and lint checks pass after the refactor stages.
- Developers report (via retro or PR feedback) that reviewing route changes now touches ≤2 focused files instead of the monolithic module.
- Documentation (README or module docstring) explains how to place new routes so onboarding engineers follow the new structure.
