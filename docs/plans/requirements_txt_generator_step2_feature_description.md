# Requirements.txt Generator - Step 2 Feature Description

Problem: Contributors sometimes need a `requirements.txt` to bootstrap environments where `pyproject.toml` tooling isn’t available, but the file can drift from the canonical dependencies. A lightweight generator keeps `requirements.txt` accurate without manual edits.

User stories:
- As a new user, I want a reliable `requirements.txt` so that I can install dependencies even if I can’t run the full CLI yet.
- As a contributor, I want `requirements.txt` to stay in sync with `pyproject.toml` so that I don’t debug mismatched installs.
- As a maintainer, I want a simple, dependency-free way to regenerate `requirements.txt` so that updates are consistent.
- As a maintainer, I want to pre-generate and commit `requirements.txt` so that the repo always has a ready-to-install snapshot.

Core requirements:
- `requirements.txt` must be derived from `pyproject.toml` so there is a single source of truth.
- Regeneration must run with only the Python standard library available.
- The flow should be explicit and repeatable (no manual edits to `requirements.txt`).
- Output format should stay stable so diffs are predictable.
- The repo should support committing a pre-generated `requirements.txt` artifact.

Shared component inventory:
- `pyproject.toml` (reuse as the canonical dependency source).
- `requirements.txt` (extend as a generated artifact; no manual edits).
- `requirements.txt` (commit the generated artifact to the repo).
- `tools/` scripts (new generator script; keep it lightweight).
- `README.md` or contributor docs (extend to document how to regenerate).

Simple user flow:
1. Contributor runs the generator script.
2. `requirements.txt` is regenerated from `pyproject.toml`.
3. User installs dependencies via `pip install -r requirements.txt` when needed.

Success criteria:
- Regenerating produces a `requirements.txt` that matches `pyproject.toml` dependencies.
- The script runs on a clean machine without extra packages.
- Team members can use `requirements.txt` to install dependencies when `pyproject.toml` tooling isn’t available.
- The repo always includes a current, committed `requirements.txt`.
