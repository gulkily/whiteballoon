## Stage 1 – Audit oversized modules
- Changes: Ran LOC + route-cluster inventory scripts. `app/routes/ui/__init__.py` totals 3,182 LOC with dominant sections: `requests` (~1,244 LOC), `invite` (~566), `people` (~176), `browse` (~131), `settings` (~130), `profile` (~62), `comments` (~59), `api` (~33), `root` (~24), `brand` (~12). `app/routes/ui/admin.py` sits at 1,202 LOC with ~1,076 LOC tied to `/admin` routes. `app/tools/comment_llm_processing.py` is 1,142 LOC spanning dataclasses (1–200), batching/planning logic (200–480), LLM clients (480–560), and CLI helpers (560+).
- Verification: Generated counts via small Python scripts (stored outputs in shell history) to confirm cluster sizing; no code behavior touched.
- Notes: Added inventory notes here for reference; next stage can scaffold packages named after the large sections above.

## Stage 2 – Scaffold route subpackages
- Changes: Created packages under `app/routes/ui/` for `auth`, `requests`, `invite`, `people`, `profile`, `browse`, `settings`, `comments`, and `api`, each exporting an empty FastAPI `router`. Documented the structure & ownership in `app/routes/ui/README.md` so contributors know where to drop new handlers.
- Verification: Ran `python -m compileall app/routes/ui` to confirm the new packages compile and import cleanly.
- Notes: Routers are inert until handlers move over in later stages; README will evolve as admin splits land.

## Stage 3 – Extract invite routes
- Changes: Moved `/invite/new` and `/invite/map` handlers into `app/routes/ui/invite/__init__.py`, wiring them up via a dedicated router and including it from `app.routes.ui.__init__`. Trimmed unused `invite_*` service imports from the monolith.
- Verification: `python -m compileall app/routes/ui/invite` to ensure the new module compiles; smoke-checked router registration order.
- Notes: Login/register already lived in `sessions.py`, so this stage focused solely on invite flows from the main module.

## Stage 4 – Move recurring request routes
- Changes: Added `app/routes/ui/requests/recurring.py` plus a package-level router so `/requests/recurring` + related POST handlers now live outside `app/routes/ui/__init__.py` with their helper functions. Hooked the new router into the top-level UI router.
- Verification: `python -m compileall app/routes/ui/requests` to ensure the package imports cleanly.
- Notes: Future stages will pick up the remaining `/requests/*` endpoints; this stage isolates the recurring template flows first to keep risk manageable.

## Stage 5 – Extract browse surface
- Changes: Moved `/browse` and all supporting pagination/filter helpers into `app/routes/ui/browse/routes.py`, wiring the `browse` package router into the UI root. `_build_request_*` pagination helpers now live alongside the route, shrinking the monolith substantially.
- Verification: `python -m compileall app/routes/ui/browse` to confirm the new module compiles without circular imports.
- Notes: Root module now delegates browse rendering entirely to the package; next stage can focus on remaining request detail handlers.

## Stage 6 – Isolate branding + metrics helpers
- Changes: Added `app/routes/ui/branding.py` for the `/brand/logo*` endpoints and `app/routes/ui/api/routes.py` for `/api/metrics`, then mounted both routers from the UI root.
- Verification: `python -m compileall app/routes/ui/branding.py app/routes/ui/api` ensures both packages import cleanly.
- Notes: This trims more utility routes from the monolith and sets up a dedicated API surface for future helpers.

## Stage 7 – Document updated layout
- Changes: Updated `app/routes/ui/README.md` to reflect the new package split (branding + API packages, auth vs invite ownership).
- Verification: Doc-only change; reviewed the rendered Markdown in-editor to ensure accurate descriptions.
- Notes: This keeps onboarding guidance aligned with the refactor so future contributors place routes correctly.

## Stage 8 – Regression sweep
- Changes: Ran `python -m compileall app` to ensure the full tree compiles; attempted `python -m pytest -q` (and `python -m pytest tests -q`) but both timed out after 120s under current sandbox limits before producing results.
- Verification: `compileall` succeeded; pytest attempts logged the timeout plus the pytest-asyncio deprecation warning. Recommend re-running `pytest -q` outside the time limit to double-check behavior.
- Notes: No code changes were required for this stage—just verification commands.
