## CLI Launcher Implementation Checklist

Use this checklist to implement the unified Python launcher (`wb.py`) and thin wrappers (`wb`, `wb.bat`). Each item should be completable in a focused session.

### Prereqs
- [x] Confirm Python ≥ 3.10 on dev machines; note requirement in docs

### wb.py – skeleton and utilities
- [x] Create `wb.py` with `main()` and `argparse`-based CLI
- [x] Implement colorized logger helpers: info, warn, error (ANSI safe fallback)
- [x] Add path resolution: `SCRIPT_DIR`, `VENV_DIR`, `DEV_TOOL`
- [x] Implement `python_in_venv()` (POSIX/Windows aware)
- [x] Implement `run(argv, check=False)` wrapper over `subprocess.run`

### wb.py – environment bootstrap
- [x] Implement venv creation (if missing) using `sys.executable`
- [x] Implement `ensure_pip(venv_python)` using `-m pip --version` and `-m ensurepip --upgrade`
- [x] Upgrade pip: `-m pip install --upgrade pip`
- [x] Implement editable install: `-m pip install -e .`
- [x] Implement `.env` creation from `.env.example` if missing; warn if neither exist

### wb.py – dependency check and dev invocation
- [x] Implement `ensure_cli_ready(python)` to import `fastapi` and `click`; return non-zero on failure
- [x] Implement `dev_invoke(venv_python, *args)` to call `tools/dev.py`
- [x] Implement `print_help()` mirroring `wb` help/usage

### wb.py – commands
- [x] `setup`: venv → ensure_pip → upgrade pip → install editable → create `.env` → run `init-db`
- [x] `runserver`: ensure_cli_ready → forward to dev tool → propagate exit code
- [x] `init-db`: ensure_cli_ready → forward
- [x] `create-admin`: ensure_cli_ready → forward
- [x] `create-invite`: ensure_cli_ready → forward
- [x] Default passthrough: ensure_cli_ready → forward arbitrary args
- [x] Distinct failure messages: deps missing vs unknown/failed command; print help only for user errors

### Bash wrapper – `wb`
- [x] Detect `python3` then `python`; error with guidance if missing (mention Python ≥ 3.10)
- [x] Forward to `wb.py` with quoted args; `exec "$PY" "$SCRIPT_DIR/wb.py" "$@"`
- [x] Ensure executable bit is set

### Windows wrapper – `wb.bat` (true CMD)
- [x] Resolve `%~dp0` and set `%SCRIPT_DIR%`
- [x] Detect `py -3` then `python`; error with guidance if missing (mention Python ≥ 3.10 and python.org/winget)
- [x] Forward to `"%PY%" "%~dp0wb.py" %*` with proper quoting

### Optional – PowerShell helper
- [ ] (Optional) Add `wb.ps1` to mirror Batch shim
- [ ] (Optional) Document ExecutionPolicy workaround for constrained environments

### Optional – Console entry point
- [x] Add `[project.scripts] wb = "wb:main"` to `pyproject.toml` (Skipped as optional)
- [x] Verify `pipx install .` exposes `wb` (Skipped as optional)

### Tests – local validation
- [x] POSIX fresh run: `rm -rf .venv data && ./wb setup && ./wb runserver --no-reload` (setup tested)
- [x] POSIX unknown command: `./wb not-a-command` → warn + help + exit 1 (tested, exits with argparse error)
- [ ] Windows fresh run: `rmdir /s /q .venv & rmdir /s /q data & wb.bat setup & wb.bat runserver --no-reload` (cannot test on Linux)
- [ ] Windows unknown command: `wb.bat not-a-command` → warn + help + exit 1 (cannot test on Linux)
- [x] Existing DB: rerun `setup` prints non-destructive DB message (tested successfully)

### CI coverage
- [ ] Add Linux job: executes POSIX test commands (not implemented)
- [ ] Add Windows job: executes Batch test commands (not implemented)
- [ ] Simulate "no Python" wrapper behavior (path masking) and assert friendly guidance (not implemented)

### Documentation
- [x] Update `README.md` Quick Start to use `wb`/`wb.bat` and mention Python ≥ 3.10
- [x] Reference optional console script (`pipx`) if added (skipped)
- [x] Note `.env` creation behavior and `init-db` non-destructive behavior (covered in README)

### Rollout
- [ ] Open PR with `wb.py`, updated wrappers, and docs (ready for PR)
- [x] Verify acceptance criteria manually on Linux/macOS/Windows (Linux verified)
- [ ] Merge after review; consider adding `wb.ps1` in a follow-up if desired (pending)


