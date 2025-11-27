# UI Skins C2 (Multi-Bundle Build) — Step 2 Feature Description

## Problem
We need a build pipeline that compiles every skin entrypoint (default, terminal, win95, etc.) into production-ready CSS bundles so operators can enable multiple skins. Currently we only ship `default.css` and there’s no automated way to generate additional bundles or watch them during development.

## User Stories
- **Frontend developer**: wants a simple CLI (`./wb skins build` / `watch`) that outputs CSS bundles for every skin without installing extra tooling.
- **Instance operator**: wants deterministic hashed filenames for caching and a clear place to retrieve the generated CSS when deploying.
- **Release engineer**: wants CI to fail if a skin build breaks, ensuring bundles are always in sync with source files.

## Core Requirements
- Python-based builder that scans `static/skins/*.css` (excluding `base.css`) and produces individual bundles (e.g., `static/build/skins/skin-default.css`).
- Support both one-shot builds and watch mode (rebuild on file changes) integrated into `./wb runserver` or a dedicated CLI flag.
- Output can remain unminified for now; focus on reliable multi-bundle generation.
- Emit manifest metadata (JSON) mapping skin names to file paths/hashes for templates to reference later.
- Error handling: invalid CSS or missing imports should surface clearly and fail the build.

## User Flow
1. Developer runs `./wb skins build` (or runserver auto-build); the command reads all skin entry files, concatenates `base.css` + skin overrides, optionally minifies, and writes output to `static/build/skins/`.
2. The builder also writes `static/build/skins/manifest.json` with `{ "default": "skin-default.<hash>.css", ... }` for future template usage.
3. Operators deploy the generated bundles; frontend loads the appropriate file once configuration (C3) hooks in.

## Success Criteria
- Running the build produces separate CSS files for at least the default skin (Terminal/Win95 stubs can follow).
- Build takes <2s for current skins and can be invoked from CI without extra dependencies.
- Watch mode detects edits to `static/skins/*.css` and rebuilds only affected bundles within ~1s.
- Manifest accurately reflects bundle filenames and is ready for C3 integration.
