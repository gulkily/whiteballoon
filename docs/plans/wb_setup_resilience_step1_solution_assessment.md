# WB Setup Resilience - Step 1 Solution Assessment

Problem statement: Ensure `./wb setup` reliably bootstraps a working environment for new users across common Python 3 versions and arbitrary preinstalled dependencies.

Option A - Managed runtime + locked deps (project-provisioned Python)
- Description: the `./wb` wrapper provisions a known Python runtime (cached per OS) and installs pinned deps inside a managed venv before running any commands.
- Pros: deterministic installs regardless of system Python quirks
- Pros: consistent dependency resolution across OSes
- Pros: simpler support with a single "known good" runtime path
- Cons: introduces a new bootstrap tool dependency
- Cons: requires platform-specific handling for runtime download/caching

Option B - Self-contained CLI bundle (packaged interpreter + deps)
- Description: ship a per-platform CLI bundle that includes a Python interpreter plus all dependencies, so `./wb` never touches system Python.
- Pros: works even without a compatible system Python
- Pros: single artifact for setup/commands
- Cons: larger distribution and release overhead
- Cons: per-platform build pipeline and updates required

Option C - System-Python tolerant setup (robust preflight + flexible deps)
- Description: keep system Python but harden `./wb setup` with version guards, smarter dependency resolution, and clearer recovery paths.
- Pros: minimal new tooling; aligns with current workflow
- Pros: faster iteration for contributors already in Python envs
- Cons: still exposed to system Python/version drift
- Cons: harder to guarantee "it just works" for new users

Recommendation: Combine Option A + Option C — default to the managed runtime for predictable installs, and keep a hardened system-Python fallback for unsupported platforms or constrained environments.
