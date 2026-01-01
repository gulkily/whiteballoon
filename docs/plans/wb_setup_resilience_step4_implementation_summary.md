## Stage 1 – Bootstrap refactor + minimal dependency surface
- Changes: added stdlib-only bootstrap helpers in `tools/wb_bootstrap.py`; refactored `wb.py` to delegate setup/venv/env creation through the new module with strategy scaffolding.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Managed runtime selection is scaffolded but defaults to system Python until later stages.

## Stage 2 – Managed runtime path (default)
- Changes: defaulted setup strategy to prefer managed runtime; added managed runtime configuration via `WB_SETUP_STRATEGY`, `WB_MANAGED_PYTHON_PATH`, `WB_MANAGED_PYTHON_URL`, `WB_MANAGED_PYTHON_VERSION`, and `WB_MANAGED_PYTHON_DIR`; implemented cached runtime download/extract flow with safe archive handling.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Managed runtime download requires a configured URL; falls back to system Python if unavailable or failing.
