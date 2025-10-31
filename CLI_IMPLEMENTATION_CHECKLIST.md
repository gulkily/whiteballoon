## CLI Launcher Implementation Checklist

Use this checklist to implement the unified Python launcher (`wb.py`) and thin wrappers (`wb`, `wb.bat`). Each item should be completable in a focused session.

### Prereqs
- [ ] Confirm Python ≥ 3.10 on dev machines; note requirement in docs

### wb.py – skeleton and utilities
- [ ] Create `wb.py` with `main()` and `argparse`-based CLI
- [ ] Implement colorized logger helpers: info, warn, error (ANSI safe fallback)
- [ ] Add path resolution: `SCRIPT_DIR`, `VENV_DIR`, `DEV_TOOL`
- [ ] Implement `python_in_venv()` (POSIX/Windows aware)
- [ ] Implement `run(argv, check=False)` wrapper over `subprocess.run`

### wb.py – environment bootstrap
- [ ] Implement venv creation (if missing) using `sys.executable`
- [ ] Implement `ensure_pip(venv_python)` using `-m pip --version` and `-m ensurepip --upgrade`
- [ ] Upgrade pip: `-m pip install --upgrade pip`
- [ ] Implement editable install: `-m pip install -e .`
- [ ] Implement `.env` creation from `.env.example` if missing; warn if neither exist

### wb.py – dependency check and dev invocation
- [ ] Implement `ensure_cli_ready(python)` to import `fastapi` and `click`; return non-zero on failure
- [ ] Implement `dev_invoke(venv_python, *args)` to call `tools/dev.py`
- [ ] Implement `print_help()` mirroring `wb` help/usage

### wb.py – commands
- [ ] `setup`: venv → ensure_pip → upgrade pip → install editable → create `.env` → run `init-db`
- [ ] `runserver`: ensure_cli_ready → forward to dev tool → propagate exit code
- [ ] `init-db`: ensure_cli_ready → forward
- [ ] `create-admin`: ensure_cli_ready → forward
- [ ] `create-invite`: ensure_cli_ready → forward
- [ ] Default passthrough: ensure_cli_ready → forward arbitrary args
- [ ] Distinct failure messages: deps missing vs unknown/failed command; print help only for user errors

### Bash wrapper – `wb`
- [ ] Detect `python3` then `python`; error with guidance if missing (mention Python ≥ 3.10)
- [ ] Forward to `wb.py` with quoted args; `exec "$PY" "$SCRIPT_DIR/wb.py" "$@"`
- [ ] Ensure executable bit is set

### Windows wrapper – `wb.bat` (true CMD)
- [ ] Resolve `%~dp0` and set `%SCRIPT_DIR%`
- [ ] Detect `py -3` then `python`; error with guidance if missing (mention Python ≥ 3.10 and python.org/winget)
- [ ] Forward to `"%PY%" "%~dp0wb.py" %*` with proper quoting

### Optional – PowerShell helper
- [ ] (Optional) Add `wb.ps1` to mirror Batch shim
- [ ] (Optional) Document ExecutionPolicy workaround for constrained environments

### Optional – Console entry point
- [ ] Add `[project.scripts] wb = "wb:main"` to `pyproject.toml`
- [ ] Verify `pipx install .` exposes `wb`

### Tests – local validation
- [ ] POSIX fresh run: `rm -rf .venv data && ./wb setup && ./wb runserver --no-reload`
- [ ] POSIX unknown command: `./wb not-a-command` → warn + help + exit 1
- [ ] Windows fresh run: `rmdir /s /q .venv & rmdir /s /q data & wb.bat setup & wb.bat runserver --no-reload`
- [ ] Windows unknown command: `wb.bat not-a-command` → warn + help + exit 1
- [ ] Existing DB: rerun `setup` prints non-destructive DB message

### CI coverage
- [ ] Add Linux job: executes POSIX test commands
- [ ] Add Windows job: executes Batch test commands
- [ ] Simulate "no Python" wrapper behavior (path masking) and assert friendly guidance

### Documentation
- [ ] Update `README.md` Quick Start to use `wb`/`wb.bat` and mention Python ≥ 3.10
- [ ] Reference optional console script (`pipx`) if added
- [ ] Note `.env` creation behavior and `init-db` non-destructive behavior

### Rollout
- [ ] Open PR with `wb.py`, updated wrappers, and docs
- [ ] Verify acceptance criteria manually on Linux/macOS/Windows
- [ ] Merge after review; consider adding `wb.ps1` in a follow-up if desired


