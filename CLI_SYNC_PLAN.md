## Goal
Bring the Windows wrapper (`wb.bat` – currently a PowerShell script) to feature parity with the Bash wrapper (`wb`).

## Current Differences (Windows vs Bash)
- Dependencies check:
  - Windows: imports `fastapi` and `typer`; fails immediately with instruction to run `./balloon.ps1 setup`.
  - Bash: imports `fastapi` and `click`; shows helpful warnings and prints help when deps missing.
- Pip bootstrap in venv:
  - Windows: assumes `pip` exists in venv.
  - Bash: bootstraps `pip` via `ensurepip` if missing, with actionable error for `python3-venv`.
- Setup behavior:
  - Windows: only installs deps and copies `.env`.
  - Bash: installs deps, copies `.env`, and also runs `init-db` (fails fast if DB init fails).
- Unknown/failed commands UX:
  - Windows: forwards to CLI; no explicit help/exit code handling on failure.
  - Bash: warns on unknown/failed commands, prints help, exits 1; distinguishes missing-deps vs unknown command.
- Help text usage line:
  - Windows: `Usage: .\balloon.ps1 <command> [options]`.
  - Bash: `Usage: ./wb <command> [options]`.
- Module reference for CLI:
  - Windows: `typer` in dependency check; actual CLI uses Click.
  - Bash: `click` in dependency check; aligns with `tools/dev.py`.

## Proposed Sync Plan
1) Align dependency checks with Click
   - In `Ensure-CliReady`, change import from `typer` to `click`.
   - On failure, show: "Dependencies missing. Run '.\\wb.bat setup' first." (or `.\\wb.ps1` if we rename).

2) Add pip bootstrap in venv
   - After creating the venv, probe: `-m pip --version`.
   - If missing, run: `-m ensurepip --upgrade`; if that fails, instruct to install Python with pip/ensurepip enabled (e.g., repair installation or enable "pip" optional feature).

3) Make `setup` run `init-db`
   - After editable install, call `tools/dev.py init-db` with the venv python.
   - Fail the setup if DB init returns non-zero.

4) Improve unknown/failed command handling
   - Wrap `Run-Dev` invocations in try/catch or use `$LASTEXITCODE` checks.
   - If command exits non-zero:
     - If failure is due to deps (from `Ensure-CliReady`), warn with next steps and print help.
     - Otherwise, warn: `Command '<name>' not recognized or failed.` then print help; exit 1.

5) Update help usage and descriptions
   - Usage line: `Usage: .\\wb.bat <command> [options]` (or `.\\wb.ps1` if we rename to PS1).
   - Update `setup` description to: "Create virtualenv, install dependencies, and initialize the database".

6) Optional: file naming cleanup
   - The current `wb.bat` contains PowerShell, not batch. Options:
     - Rename to `wb.ps1` and update docs, or
     - Replace with a true `.bat` (cmd) wrapper that shells out to `powershell -ExecutionPolicy Bypass -File wb.ps1`.

7) Exit codes and colors
   - Ensure non-zero exit on failure paths (unknown command, deps missing, DB init fail).
   - Keep colorized messages consistent with Bash (Info=blue, Warn=yellow, Error=red).

## Implementation Steps (ordered)
1. Update `Ensure-CliReady` to import `click` (not `typer`) and adjust message.
2. In `Setup-Cmd`:
   - After venv creation, add pip bootstrap via `ensurepip` fallback.
   - Keep `pip install --upgrade pip` and `pip install -e .`.
   - Add `init-db` call; on failure, exit 1 with clear message.
3. Wrap all `Run-Dev` calls:
   - If `Ensure-CliReady` fails, print help and exit 1.
   - After running, if `$LASTEXITCODE -ne 0`, print help and exit 1 with a tailored message.
4. Update `Print-Help` usage line and `setup` description.
5. (Optional) Rename to `wb.ps1` and add a thin `wb.bat` shim for cmd users.

## Test Matrix
- Fresh machine with no venv:
  - `.\n+wb.bat setup` → creates venv, bootstraps pip if needed, installs deps, initializes DB, prints success.
  - `.
wb.bat runserver` → starts server.
- Missing deps:
  - `.
wb.bat runserver` before setup → warns and prints help.
- Unknown command:
  - `.
wb.bat not-a-command` → warns, prints help, exits 1.
- Existing DB:
  - `.
wb.bat setup` → DB init succeeds; no data loss.

## Notes
- The Python CLI is Click-based (`tools/dev.py`). Aligning the dependency check to `click` removes confusion.
- On Windows, `ensurepip` availability depends on the Python distribution; include actionable guidance if it’s missing.

## Python Launcher Consolidation Plan (keep `wb`/`wb.bat` wrappers)

### Objectives
- Single cross-platform implementation in Python (`wb.py`) for all logic.
- Retain a Bash wrapper (`wb`) and a Batch wrapper (`wb.bat`) that:
  - Provide a clear, friendly message when Python isn’t installed.
  - Otherwise defer to `wb.py` passing through all arguments.

### Deliverables
1) `wb.py` (new): unified launcher providing parity with current Bash script
   - Detect or create `.venv` using the base interpreter.
   - Bootstrap `pip` via `ensurepip` if missing; upgrade `pip`.
   - Install project in editable mode (`-e .`).
   - Create `.env` from `.env.example` if missing.
   - `setup` subcommand also runs `init-db` and fails on error.
   - Forward commands to `tools/dev.py` (either via `subprocess` or by importing the Click CLI and invoking programmatically).
   - Clear, colored/stdout messages mirroring `wb` behavior; exit codes consistent.

2) `wb` (Bash wrapper): thin shim with Python presence check
   - If `python3`/`python` missing: print actionable instructions (Linux/macOS) and exit 1.
   - Else: `exec "$PY" "$SCRIPT_DIR/wb.py" "$@"`.

3) `wb.bat` (true cmd batch wrapper): thin shim with Python presence check
   - Try `py -3` first (Windows Launcher), then `python`.
   - If neither found: print friendly message with install guidance (link to python.org / winget command) and exit /b 1.
   - Else: `"%PY%" "%~dp0wb.py" %*`.
   - Optional: also ship `wb.ps1` for PowerShell users; `.bat` can detect PowerShell availability and delegate, but not required.

4) Optional console entry point
   - Add to `pyproject.toml`:
     - `[project.scripts] wb = "wb:main"` so `pipx install .` exposes a native `wb`.
   - Keep wrappers for users running from a fresh checkout without global installs.

### Migration Steps
1. Implement `wb.py` with subcommands: `setup`, `runserver`, `init-db`, `create-admin`, `create-invite`, and a passthrough default.
2. Replace current `wb.bat` content (PowerShell) with true Batch shim; optionally add `wb.ps1` (PowerShell) mirroring the Batch shim.
3. Update existing `wb` Bash script to defer to `wb.py` (retain current helpful messages if Python/venv missing).
4. Update help text in all entry points to show `Usage: wb <command> [options]`.
5. (Optional) Add console entry point in `pyproject.toml`.
6. Test on:
   - Linux/macOS without venv (fresh clone).
   - Windows with `py` launcher; Windows without `py` but with `python`.
   - Systems without Python: verify wrappers show guidance and exit non-zero.
   - Existing DB vs new DB for `setup` and `init-db` messages.

### Testing Matrix (concise)
- No Python installed:
  - `./wb` → friendly install guidance; exit 1
  - `wb.bat` → friendly install guidance; exit 1
- Fresh environment:
  - `./wb setup` → venv created, pip bootstrapped, deps installed, DB initialized
  - `wb.bat setup` → same as above
- Post-setup:
  - `./wb runserver` / `wb.bat runserver` → server starts
- Unknown command:
  - Both wrappers print warning + help, exit 1

### Rationale
- One Python implementation eliminates drift and reduces maintenance.
- Thin wrappers preserve great UX on machines missing Python and keep familiar `wb`/`wb.bat` entry points.


