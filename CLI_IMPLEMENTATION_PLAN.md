## Objective
Implement a single cross‑platform Python launcher (`wb.py`) and keep thin `wb` (Bash) and `wb.bat` (Batch) wrappers that: (a) show a friendly message if Python is missing, and (b) otherwise forward to `wb.py`. Achieve feature parity with the current Bash wrapper and Windows plan in `CLI_SYNC_PLAN.md`.

## Deliverables
1) `wb.py` – Python entrypoint providing commands: `setup`, `runserver`, `init-db`, `create-admin`, `create-invite`, plus default passthrough to `tools/dev.py`.
2) Updated `wb` – Bash wrapper that checks Python availability and forwards to `wb.py` with all args.
3) Updated `wb.bat` – true CMD batch wrapper (not PowerShell) that checks `py -3`/`python` and forwards to `wb.py` with all args.
4) Optional: `wb.ps1` – PowerShell helper mirroring Batch logic (only if we want a native PS experience).
5) Optional: `pyproject.toml` console entry point – expose `wb` when installed via `pipx` or editable install.

## Functional Requirements
- `setup`:
  - Create `.venv` (if missing) using the base interpreter.
  - Ensure `pip` exists in the venv (via `ensurepip`), then `pip install --upgrade pip`.
  - `pip install -e .` the project.
  - Create `.env` from `.env.example` if missing.
  - Run `init-db` and fail setup if it returns non‑zero.
- `runserver`, `init-db`, `create-admin`, `create-invite`:
  - Forward to `tools/dev.py` through the venv interpreter.
- Unknown commands:
  - Forward to `tools/dev.py` and if non‑zero exit, print helpful message + `wb` help and exit 1.
- Dependency check:
  - Import `fastapi` and `click` (not Typer). If missing, instruct to run `./wb setup` first.
- Messages and exit codes align with current `wb` UX.

## Implementation Steps
1) Create `wb.py` with structure:
   - Detect base Python: prefer `sys.executable`; allow override via env `WB_PYTHON`.
   - Paths: resolve `SCRIPT_DIR`, `VENV_DIR = .venv`, `DEV_TOOL = tools/dev.py`.
   - Logger helpers for info/warn/error (colorized on ANSI terminals; fallback to plain text on Windows if needed).
   - Helpers:
     - `run([argv], check=False)` wrapper around `subprocess.run`.
     - `python_in_venv()` returns `VENV_DIR/bin/python` (POSIX) or `VENV_DIR/Scripts/python.exe` (Windows).
     - `ensure_pip(venv_python)` tries `-m pip --version`; if missing, run `-m ensurepip --upgrade` and recheck.
     - `create_env_file()` copies `.env.example` → `.env` if missing.
     - `ensure_cli_ready(base_or_venv_python)` executes a tiny script importing `fastapi` and `click`.
     - `dev_invoke(venv_python, *args)` runs `tools/dev.py` with args and returns exit code.
   - Commands:
     - `setup`: create venv if missing → ensure_pip → upgrade pip → install editable → create_env_file → run `init-db` via `dev_invoke` → success message.
     - `runserver|init-db|create-admin|create-invite`: ensure_cli_ready → dev_invoke; on failure print help and exit 1.
     - Default passthrough: same as above with arbitrary args.
   - Help output mirrors `wb` help (usage + core commands + note about forwarding).

2) Update `wb` Bash wrapper:
   - Detect python: `command -v python3 || command -v python`.
   - If missing: print friendly instructions and exit 1.
   - Else: `exec "$PY" "$SCRIPT_DIR/wb.py" "$@"`.
   - Keep file executable (`chmod +x wb`).

3) Replace `wb.bat` contents with true CMD batch:
   - Try `py -3` then `python` into `%PY%`.
   - If not found: echo friendly guidance (python.org / winget) and `exit /b 1`.
   - Else: `"%PY%" "%~dp0wb.py" %*`.
   - Note: We can optionally also ship a `wb.ps1` for PowerShell-first users, but `.bat` is sufficient.

4) Optional console script entry point:
   - In `pyproject.toml`, add:
     - `[project.scripts]\nwb = "wb:main"`
   - Implement `main()` in `wb.py` to parse CLI and dispatch.

## File-by-File Tasks
- `wb.py` (new):
  - Implement CLI using `argparse` or `click` (either okay; `argparse` avoids dependency coupling, but using stdlib keeps launcher minimal). The launcher should not depend on project packages being installed to print help and run `setup`.
  - Use `subprocess` to invoke `tools/dev.py` for subcommands; avoid importing project modules inside the launcher except when checking deps after setup.

- `wb` (Bash):
  - Replace body with: python detection + forward to `wb.py`. Keep current colors only for error message when Python missing.

- `wb.bat` (Batch):
  - Replace PowerShell content with CMD as described.

- `pyproject.toml` (optional):
  - Add console entry point stanza.

## Acceptance Criteria
- Fresh checkout on Linux/macOS without `.venv`:
  - `./wb setup` creates venv, bootstraps pip, installs, creates `.env` (if missing), initializes DB, exits 0.
  - `./wb runserver` starts server.
- Fresh checkout on Windows with only `py` launcher:
  - `wb.bat setup` performs the same as above.
  - `wb.bat runserver` starts server.
- Missing Python:
  - `./wb` prints guidance and exits 1.
  - `wb.bat` prints guidance and exits 1.
- Existing DB:
  - `setup` runs `init-db` and prints non‑destructive message; no data loss.
- Unknown command:
  - Both wrappers forward to `wb.py`; on failure, print warning + help and exit 1.

## Refinements and Edge Cases
- Python version requirement
  - Require Python ≥ 3.10 (matches `pyproject.toml`). Wrappers should mention this in the missing-Python guidance.

- Launcher parser choice
  - Use stdlib `argparse` in `wb.py` to avoid adding dependencies. Do not import project modules to render help or perform `setup`.

- Windows `ensurepip` guidance
  - If `-m ensurepip --upgrade` is unavailable or fails, print: "Python installation lacks ensurepip. Repair Python and enable pip, or reinstall from python.org with Add to PATH and pip enabled." Also suggest:
    - `py -3 -m ensurepip --upgrade`
    - `py -3 -m pip install --upgrade pip`

- PowerShell execution policy
  - Only applicable if we add `wb.ps1`. If added, document: `PowerShell -ExecutionPolicy Bypass -File wb.ps1 setup` for constrained environments.

- Path robustness
  - Quote all paths with potential spaces in wrappers and in `wb.py` subprocess calls.

- Interpreter preference order
  - POSIX: prefer `python3`, then `python`.
  - Windows: prefer `py -3`, then `python`.

- Failure messaging
  - Print `wb` help only for user errors (unknown command, bad args). For internal exceptions, show concise error and suggest re-running with `--verbose` (future), but do not spam help. Keep distinct messages for "dependencies missing" vs "unknown command".

- CI coverage
  - Add jobs for Linux and Windows runners to execute the Test Commands matrix: `setup`, `runserver`, unknown command, and wrapper behavior when Python is missing (simulated by path masking).

- .env fallback behavior
  - If neither `.env` nor `.env.example` exists, print a warning that `.env` was not created and continue.

## Test Commands
- POSIX:
  - `rm -rf .venv data && ./wb setup && ./wb runserver --no-reload`
  - `./wb not-a-command` (expect help + exit 1)

- Windows (CMD):
  - `rmdir /s /q .venv & rmdir /s /q data & wb.bat setup & wb.bat runserver --no-reload`
  - `wb.bat not-a-command` (expect help + exit 1)

## Rollout Plan
1) Land `wb.py` and wrappers behind PR.
2) Validate on Linux, macOS, and Windows runners (or local VMs).
3) Update `README.md` quick start to reference `wb`/`wb.bat` and `pipx` console script (if added).
4) After stabilization, consider removing PowerShell content from repo or adding optional `wb.ps1`.


