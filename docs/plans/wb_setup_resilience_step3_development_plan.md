# WB Setup Resilience - Step 3 Development Plan

1) Bootstrap refactor + minimal dependency surface
- Goal: keep `wb.py` lightweight while exposing a clear setup orchestration API.
- Dependencies: existing `wb.py`, `wb`, `wb.bat`.
- Expected changes: split setup orchestration into a small internal module (stdlib-only) and keep `wb.py` as a thin entrypoint; introduce planned signatures such as `select_setup_strategy(ctx) -> SetupStrategy`, `ensure_managed_runtime(ctx) -> RuntimeStatus`, `ensure_system_python(ctx) -> Path`, `run_setup(ctx, python_path) -> int`.
- Verification: run `./wb --help` and `./wb setup` in a clean repo clone to ensure the entrypoint still executes.
- Risks/open questions: avoiding any import of app modules before deps install; path layout for new bootstrap module.
- Canonical components touched: `wb.py`, `wb`, `wb.bat`.

2) Managed runtime path (default)
- Goal: add a default setup path that provisions a known-good Python runtime with caching.
- Dependencies: Stage 1 bootstrap refactor.
- Expected changes: runtime acquisition logic, cache directory policy, and a strategy selector (auto/managed/system); introduce optional env/config overrides for runtime selection.
- Verification: smoke test `./wb setup` with no system Python or with a mismatched version to confirm managed path is selected and completes.
- Risks/open questions: platform-specific runtime sources; offline/airgapped behavior; download size.
- Canonical components touched: `wb.py`, new bootstrap module, `README.md`.

3) System Python fallback hardening
- Goal: improve resilience when managed runtime is unavailable.
- Dependencies: Stage 1 bootstrap refactor.
- Expected changes: stricter preflight checks (version, `venv`/pip availability), clearer error messages, and safe repair/retry behavior when a venv is partially broken.
- Verification: simulate missing `venv`/pip and verify guidance; rerun `./wb setup` after a failed install.
- Risks/open questions: handling distro-specific missing packages; preserving existing local state vs. repair behavior.
- Canonical components touched: `wb.py`, `README.md`.

4) Dependency install strategy alignment
- Goal: make dependency installs deterministic without requiring `requirements.txt`.
- Dependencies: Stage 2/3 runtime selection.
- Expected changes: standardize on `pyproject.toml` as the source of truth; add optional lock/constraints support if present; ensure installs are isolated and repeatable.
- Verification: confirm `./wb setup` succeeds with preinstalled global packages and without a `requirements.txt` file.
- Risks/open questions: whether to generate/commit a lock file vs. allow floating resolution; handling local editable install behavior.
- Canonical components touched: `pyproject.toml`, `wb.py`.

5) Diagnostics and user-facing messaging
- Goal: make failures actionable and reduce support churn.
- Dependencies: Stages 2–4.
- Expected changes: structured error output identifying the chosen setup path, detected Python version, and next-step guidance; optional `./wb setup --diagnose` summary output.
- Verification: run failure scenarios and confirm the printed guidance matches expected recovery steps.
- Risks/open questions: balancing verbosity vs. clarity; ensuring messages stay accurate across platforms.
- Canonical components touched: `wb.py`, `README.md`.

6) Documentation updates
- Goal: keep onboarding aligned with the new setup behavior.
- Dependencies: Stages 1–5.
- Expected changes: update `README.md` and `AI_PROJECT_GUIDE.md` to describe the managed runtime default and fallback path; document any new flags or env overrides.
- Verification: manual doc review and quick start walkthrough using the updated steps.
- Risks/open questions: avoiding drift between docs and CLI behavior.
- Canonical components touched: `README.md`, `AI_PROJECT_GUIDE.md`.
