# Step 3 – Development Plan: Python Source Refactor

1. **Audit oversized modules**
   - *Goal*: Confirm current LOC counts and map cohesive route/helper clusters inside `app/routes/ui/__init__.py`, `app/routes/ui/admin.py`, and `app/tools/comment_llm_processing.py`.
   - *Dependencies*: step2 description; repo at head.
   - *Changes*: Produce a short inventory (notes only) of logical sections (e.g., “auth routes,” “requests feed routes”) and their approximate LOC to inform extraction order.
   - *Verification*: Sanity check with `wc -l` on the target files; no code changes yet.
   - *Risks*: Missed dependencies if we overlook helper call sites; mitigate by tracing imports during the audit.

2. **Create route subpackages**
   - *Goal*: Establish new packages (e.g., `app/routes/ui/auth/`, `app/routes/ui/requests/`, `app/routes/ui/admin/sections/`) with `__init__.py` files exposing `router` objects.
   - *Dependencies*: Stage 1 inventory to pick package names.
   - *Changes*: Add empty scaffolds plus module docstrings describing responsibilities; update `pyproject` if namespace packages need inclusion.
   - *Verification*: Run `pytest -q` (or at least `python -m compileall app/routes/ui`) to ensure imports resolve.
   - *Risks*: Package layout churn could confuse tooling; document the structure in a README within `app/routes/ui/`.

3. **Extract authentication routes**
   - *Goal*: Move all login/register/invite handlers from `app/routes/ui/__init__.py` into `app/routes/ui/auth/routes.py`.
   - *Dependencies*: Stage 2 packages exist.
   - *Changes*: Relocate functions, share common dependencies via a new `app/routes/ui/auth/deps.py` if needed, and re-export a cohesive `APIRouter`.
   - *Verification*: Run targeted tests (`pytest tests/auth` or nearest equivalent) and hit `/login` locally to confirm behavior.
   - *Risks*: Circular imports if helpers still live in the root file; break cycles by passing dependencies via parameters instead of module-level imports.

4. **Extract requests + members routes**
   - *Goal*: Move feed/detail/member-facing routes into new modules (`requests/routes.py`, `members/routes.py`).
   - *Dependencies*: auth extraction complete so shared helpers are obvious.
   - *Changes*: Split per-surface logic, keep route tags/paths identical, and adjust template imports if necessary.
   - *Verification*: `pytest tests/requests` (or smoke `/requests` UI in dev server); ensure `uvicorn` startup logs show routes registered once.
   - *Risks*: Hidden helper functions (e.g., pagination) might still live in the root file; create shared helper modules (`app/routes/ui/shared.py`) where duplication appears.

5. **Decompose admin surface**
   - *Goal*: Shrink `app/routes/ui/admin.py` by splitting panels (ledger, profiles, dedalus) into dedicated modules.
   - *Dependencies*: Stage 2 packages for admin; earlier stages ensure helper placement.
   - *Changes*: For each admin area create `app/routes/ui/admin/{area}.py`, moving both route handlers and adjacent helper functions; leave `admin.py` as an orchestrator that mounts subrouters.
   - *Verification*: Open `/admin` pages manually and ensure navigation works; run any admin-focused tests.
   - *Risks*: Permissions decorators might rely on module globals; verify `Depends(require_admin)` still imports cleanly.

6. **Split comment processing tooling**
   - *Goal*: Break `app/tools/comment_llm_processing.py` into smaller modules (e.g., `prompting.py`, `formatters.py`, `cli.py`).
   - *Dependencies*: None beyond stage 1 knowledge.
   - *Changes*: Identify clusters (prompt templates vs. IO) and move into separate files under `app/tools/comment_processing/`, updating imports in CLI entry points.
   - *Verification*: Run the existing CLI/module tests or sample commands (`python -m app.tools.comment_processing.cli --help`).
   - *Risks*: Hidden global state; ensure constants stay in one module and are imported, not duplicated.

7. **Document new structure**
   - *Goal*: Capture contributor guidance so future routes/tools land in the right files.
   - *Dependencies*: Structural changes complete.
   - *Changes*: Update `docs/DEV_CHEATSHEET.md` or add `app/routes/README.md` describing package layout and naming conventions; include pointers for tooling modules too.
   - *Verification*: Peer review doc; ensure references point to existing paths.
   - *Risks*: Documentation drifting if we forget to update when new sections appear—note follow-up tasks in `actionable_tasks.md`.

8. **Regression sweep**
   - *Goal*: Prove the refactor is behavior-neutral.
   - *Dependencies*: All code moves done.
   - *Changes*: Run suite (`pytest`, lint, `wb dev server` smoke), verify FastAPI startup route list, and ensure CLI entry points (wb.py) still function.
   - *Verification*: Record command outputs and capture any issues for follow-up bugs.
   - *Risks*: Subtle import-order regressions; consider enabling `PYTHONWARNINGS=error` to catch them early.
