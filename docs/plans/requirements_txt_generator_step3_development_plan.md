# Requirements.txt Generator - Step 3 Development Plan

1) Generator script scaffolding
- Goal: create a stdlib-only script that reads `pyproject.toml` and emits a stable `requirements.txt`.
- Dependencies: `pyproject.toml` dependency list.
- Expected changes: add a script under `tools/` with signatures like `load_dependencies(pyproject_path) -> list[str]`, `render_requirements(deps) -> str`, `write_requirements(path, content) -> None`.
- Verification: run the script and confirm `requirements.txt` is regenerated with expected lines.
- Risks/open questions: handling optional dependencies/extras; ordering rules for predictable output.
- Canonical components touched: `pyproject.toml`, `tools/` scripts, `requirements.txt`.

2) CLI/documentation hook
- Goal: document and expose the generator for maintainers.
- Dependencies: Stage 1 script.
- Expected changes: update `README.md` or contributor docs; optionally add a `./wb` passthrough or a `tools/dev.py` command that runs the script.
- Verification: follow docs to regenerate `requirements.txt` end-to-end.
- Risks/open questions: whether to add a CLI entry point vs. run the script directly.
- Canonical components touched: `README.md`, `tools/dev.py` (if adding a command).

3) Committed artifact workflow
- Goal: ensure the repo includes a pre-generated `requirements.txt` and the regeneration flow is explicit.
- Dependencies: Stage 1 output format.
- Expected changes: add/update `requirements.txt` in the repo; note in docs that it is generated and should not be edited manually.
- Verification: diff `requirements.txt` after script run to confirm stability.
- Risks/open questions: aligning generator output with existing `requirements.txt` expectations; avoiding accidental manual edits.
- Canonical components touched: `requirements.txt`, documentation.
