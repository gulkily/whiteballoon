## Stage 1 – Bootstrap refactor + minimal dependency surface
- Changes: added stdlib-only bootstrap helpers in `tools/wb_bootstrap.py`; refactored `wb.py` to delegate setup/venv/env creation through the new module with strategy scaffolding.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Managed runtime selection is scaffolded but defaults to system Python until later stages.
