## Stage 1 – Bootstrap refactor + minimal dependency surface
- Changes: added stdlib-only bootstrap helpers in `tools/wb_bootstrap.py`; refactored `wb.py` to delegate setup/venv/env creation through the new module with strategy scaffolding.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Managed runtime selection is scaffolded but defaults to system Python until later stages.

## Stage 2 – Managed runtime path (default)
- Changes: defaulted setup strategy to prefer managed runtime; added managed runtime configuration via `WB_SETUP_STRATEGY`, `WB_MANAGED_PYTHON_PATH`, `WB_MANAGED_PYTHON_URL`, `WB_MANAGED_PYTHON_VERSION`, and `WB_MANAGED_PYTHON_DIR`; implemented cached runtime download/extract flow with safe archive handling.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Managed runtime download requires a configured URL; falls back to system Python if unavailable or failing.

## Stage 3 – System Python fallback hardening
- Changes: added system Python preflight checks for version/venv/ensurepip and improved broken-venv repair handling when falling back to system Python.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: System Python must be 3.10+ or setup exits with actionable guidance to use a managed runtime.

## Stage 4 – Dependency install strategy alignment
- Changes: added optional pip constraints support via `WB_PIP_CONSTRAINTS` or local `constraints.txt`/`requirements.lock`, while continuing to install from `pyproject.toml` via editable install.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Setup remains independent of a `requirements.txt` file; constraints are opt-in.

## Stage 5 – Diagnostics and user-facing messaging
- Changes: added setup diagnostics output (`./wb setup --diagnose`), including requested/resolved strategy, Python version, and active constraints file; improved warnings when falling back to system Python.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Diagnostics run before setup and exit early when `--diagnose` is used.

## Stage 6 – Documentation updates
- Changes: documented managed runtime setup options in `README.md`, `AI_PROJECT_GUIDE.md`, and `.env.example`.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Docs now call out optional constraints and strategy overrides.
