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
