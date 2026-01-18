## Stage 1 – Generator script scaffolding
- Changes: added `tools/generate_requirements.py` to derive `requirements.txt` from `pyproject.toml` using stdlib-only parsing with a tomllib fast path.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: Falls back to a minimal parser on Python 3.10 where tomllib is unavailable.

## Stage 2 – CLI/documentation hook
- Changes: added `./wb generate-requirements` passthrough and documented regeneration guidance in `README.md`.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: The script can also be run directly via `python tools/generate_requirements.py`.

## Stage 3 – Committed artifact workflow
- Changes: updated `requirements.txt` header to mark it as generated and aligned the generator header output accordingly.
- Verification: Not run (per project guidance to avoid running commands).
- Notes: The committed artifact now matches the generator output format.
