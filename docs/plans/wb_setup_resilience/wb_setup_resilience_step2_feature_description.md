# WB Setup Resilience - Step 2 Feature Description

Problem: New users running `./wb setup` encounter dependency errors because their system Python or existing packages vary. The setup flow should succeed (or fail clearly) across common Python 3 versions without manual cleanup.

User stories:
- As a new user, I want `./wb setup` to just work on my machine so that I can start the app without debugging Python packaging.
- As a contributor, I want setup to be idempotent so that rerunning it fixes a broken environment without extra steps.
- As a maintainer, I want a predictable setup path so that support and docs stay consistent across platforms.
- As a power user, I want a safe fallback when the managed path is unavailable so that I can still bootstrap locally.
- As a maintainer, I want the bootstrap script to stay lightweight and modular so that setup can run before project dependencies are installed.

Core requirements:
- `./wb setup` succeeds on common Python 3 versions (3.8–3.12) without requiring global installs.
- Setup tolerates preinstalled dependencies and does not rely on a `requirements.txt` file.
- A managed runtime path is the default, with a hardened system-Python fallback when the managed path cannot run.
- Failures explain the next step clearly (missing runtime, unsupported OS, or dependency resolution issues).
- The flow remains safe to re-run without breaking existing local state.
- The bootstrap entrypoint stays minimal in dependencies so it can run on a clean machine.

Shared component inventory:
- `./wb setup` command (extend the existing setup behavior; keep it the canonical entry point).
- `wb` and `wb.bat` wrappers (reuse; adjust only to route to the preferred setup path).
- `wb.py` bootstrap logic (extend; remains the primary setup orchestrator and stays lightweight).
- `tools/dev.py` CLI entrypoint (reuse; no new CLI surface unless required).
- Dependency metadata in `pyproject.toml` (reuse as the canonical source of install requirements).
- `README.md` quick start + `AI_PROJECT_GUIDE.md` setup notes (extend to document the new behavior).

Simple user flow:
1. User runs `./wb setup` (or `wb.bat setup` on Windows).
2. The CLI selects the best setup path and validates compatibility.
3. The environment is prepared and dependencies are installed.
4. The CLI confirms success and points to the next command (e.g., `./wb runserver`).

Success criteria:
- Fresh installs on macOS, Linux, and Windows with Python 3.10–3.12 complete `./wb setup` without dependency errors.
- Rerunning `./wb setup` after a partial or failed install results in a clean, working environment.
- Unsupported Python versions or environments show a clear, actionable error message.
- Docs reflect the new setup behavior and no longer suggest manual dependency steps for first-time users.
