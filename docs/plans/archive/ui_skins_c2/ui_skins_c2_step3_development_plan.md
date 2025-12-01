# UI Skins C2 (Multi-Bundle Build) — Step 3 Development Plan

## Stage 1 – Builder CLI skeleton
- **Goal**: Add a Python CLI command (`./wb skins build` + `--watch`) that discovers skin entry files and orchestrates builds.
- **Changes**: Update `wb.py` / dev tooling to include `skins` subcommand; parse flags for `build`, `watch`, `--output-dir`, `--manifest`.
- **Verification**: Running `./wb skins build --dry-run` lists detected skins.
- **Risks**: CLI clutter; ensure errors propagate cleanly.

## Stage 2 – Bundle generation logic
- **Goal**: Implement the actual concatenation pipeline.
- **Changes**: For each skin (excluding base), read `base.css` first, then the skin file, combine them, and write to `static/build/skins/<skin>.css`. Compute content hash for filenames (e.g., `skin-default.<hash>.css`). Emit manifest JSON mapping skin key → filename + hash.
- **Verification**: After running build, confirm files exist with expected names; diff default bundle vs previous single CSS for sanity.
- **Risks**: Hash collisions, file permissions, forgetting to clean old bundles.

## Stage 3 – Watch mode integration
- **Goal**: Provide a dev workflow that rebuilds on change.
- **Changes**: Use `watchdog` (or polling fallback) to monitor `static/skins/*.css`. Rebuild only affected skin or all (simpler). Ensure graceful shutdown. Optionally integrate with `./wb runserver` so watch mode auto-starts when server runs.
- **Verification**: Modify `static/skins/default.css`; watch logs show rebuild and output timestamp. No excessive rebuild loops.
- **Risks**: Watcher missing events on some platforms; need debouncing to avoid thrash.

## Stage 4 – CI / documentation
- **Goal**: Document usage and wire into CI.
- **Changes**: Update `docs/skins/token_inventory.md` (or new doc) with build instructions. Add CI step (or manual checklist) to run `./wb skins build`. Mention artifact paths in README.
- **Verification**: `README` snippet reviewed; CI script (if exists) updated; manual smoke test ensures docs accurate.
- **Risks**: Forgetting to update future C3 templates with manifest usage (tracked separately).

## Verification Plan
- Manual: run `./wb skins build` and `./wb skins watch`.
- Automated: add unit test for manifest generation (if practical). Otherwise rely on CI command exit status.
