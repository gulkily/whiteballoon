## Stage 1 – Generator script scaffolding
- Changes: added `tools/generate_requirements.py` to derive `requirements.txt` from `pyproject.toml` using stdlib-only parsing with a tomllib fast path.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Falls back to a minimal parser on Python 3.10 where tomllib is unavailable.
