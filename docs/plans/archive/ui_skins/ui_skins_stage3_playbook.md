# UI Skins — Stage 3 Implementation Playbook

## Capability C1 – Core Style Extraction
- **Tasks**:
  1. Inventory all color/typography/layout tokens used in `static/css/app.css`; identify hard-coded values.
  2. Split shared utilities/layout into `static/skins/base.css` (or SCSS) partial; replace literals with CSS variables (e.g., `--skin-bg`, `--skin-border`).
  3. Verify `skin-default.css` (base + overrides) reproduces current UI via visual smoke test.
- **Data/API changes**: None.
- **Verification**: Pixel-compare screenshots (manual) for key pages (home, request list, invite map). Run existing frontend lint/build.
- **Feature flag**: N/A (pure refactor but keep behind branch).
- **Logging/Instrumentation**: None.
- **Rollout**: Merge once baseline matches production.

## Capability C2 – Multi-Bundle Build System
- **Tasks**:
  1. Update build scripts (npm or Python tooling) to accept a skin manifest and emit `skin-*.css` bundles with hashed filenames.
  2. Create entrypoints for `default`, `terminal`, `win95` skins referencing base partial and their specific overrides.
  3. Ensure `./wb runserver` dev pipeline watches all skin files; CI builds all bundles.
- **Data/API changes**: None.
- **Verification**: Build command outputs three bundles; file sizes within budget; dev server hot reload works.
- **Feature flag**: Optional env `WB_SKINS_BUILD=default,terminal,win95` for limiting builds during dev.
- **Logging**: Build logs list generated bundles.

## Capability C3 – Operator Configuration & Serving
- **Tasks**:
  1. Add server-side config (env or settings file) specifying allowed skins + default.
  2. Update base template to render `<link rel="stylesheet" data-skin="...">` tags per allowed skin (async/deferred for non-default) and expose skin metadata to JS (e.g., `window.__skins`).
  3. Add backend validation + friendly errors when configured skin bundle missing.
- **Data/API changes**: Possibly extend `/settings` endpoint or config module.
- **Verification**: Toggle config to include/exclude skins and confirm template only includes valid ones. Check server logs on missing file scenarios.
- **Feature flag**: `WB_SKINS_ENABLED=true` to gate UI until ready.
- **Instrumentation**: log currently selected skin/default at startup.

## Capability C4 – Frontend Skin Selector & Loader
- **Tasks**:
  1. Extend existing theme toggle (or add dropdown) listing available skins; design for desktop/mobile.
  2. Implement JS loader that swaps `<link>` (or `disabled` attributes) to activate chosen skin without reload, persisting preference (localStorage/URL param) and honoring default on fresh load.
  3. Ensure interplay with auto/light/dark behavior per skin (maybe each skin supplies two variants or we pause auto-mode for non-default).
- **Data/API changes**: None beyond window config JSON.
- **Verification**: Manual QA switching among Default/Terminal/Win95; confirm no FOUC, check ARIA, ensure fallback to default when JS disabled.
- **Feature flag**: UI hidden unless `WB_SKINS_ENABLED` and >1 skin configured.
- **Instrumentation**: optional event logging when user changes skin.

## Capability C5 – Skin Authoring Toolkit
- **Tasks**:
  1. Add CLI command (`./wb skins create <name>`) scaffolding new entrypoint + config stub.
  2. Document skin folder structure, variables, and testing checklist in `docs/`.
  3. Support dev server overrides (`./wb runserver --skin win95`) plus query param `?skin=terminal` for quick previews (guarded in prod).
  4. Optional lint to ensure new skin imports base partial and defines mandatory tokens.
- **Verification**: Run CLI to create sample skin; preview via dev server; documentation reviewed.
- **Feature flag**: Query param preview allowed only when `WB_SKINS_PREVIEW=1`.
- **Instrumentation**: Document how to enable analytics per skin if desired.
