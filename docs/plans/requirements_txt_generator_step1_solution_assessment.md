# Requirements.txt Generator - Step 1 Solution Assessment

Problem statement: Keep `requirements.txt` in sync with `pyproject.toml` without manual edits or drift.

Option A - Stdlib generator script (parse pyproject and render requirements.txt)
- Pros: no extra dependencies; runs before installs
- Pros: deterministic and easy to audit
- Cons: limited to basic dependency extraction (no resolution)
- Cons: must maintain formatting rules manually

Option B - Tool-backed generator (uv/pip-compile wrapper)
- Pros: handles markers, extras, and resolution consistently
- Pros: less custom logic to maintain
- Cons: adds a new tool dependency and versioning burden
- Cons: may require network access or extra config

Option C - Drop requirements.txt and document `pyproject.toml` as canonical only
- Pros: zero additional tooling or scripts
- Pros: avoids duplicate sources of truth entirely
- Cons: breaks workflows that expect requirements.txt
- Cons: conflicts with environments that can’t consume `pyproject.toml` directly

Recommendation: Option A, because it keeps setup lightweight and matches the goal of avoiding extra dependencies while still supporting tools that need `requirements.txt`.
