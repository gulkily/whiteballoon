# UI Skins C3 (Config & Serving) — Step 1 Solution Assessment

## Problem
We now produce hashed skin bundles + manifest, but the frontend still hard-codes `/static/skins/default.css`. Instance operators cannot choose Terminal/Win95 skins (or change the default) without editing templates. We need a configuration mechanism and template wiring that loads the desired bundle using the manifest metadata.

## Option A – Environment variables + manifest lookup (preferred)
- **Approach**: Introduce `WB_SKINS_ENABLED`, `WB_SKIN_DEFAULT`, and `WB_SKINS_ALLOWED` env vars (or settings). On startup, backend reads `static/build/skins/manifest.json`, validates configured skins, and passes the resolved bundle URL(s) into templates/context. Templates render `<link>` tags based on this context. Optional query param `?skin=` for preview.
- **Pros**: Simple deploy-time config, no DB migration, integrates cleanly with existing settings model, works for CLI/server flows.
- **Cons**: Requires restart to change default; operators must remember to rebuild bundles before toggling.

## Option B – JSON config file + hot reload
- **Approach**: Store skin settings in a JSON config (
  e.g., `config/skins.json`). App watches the file and updates served bundle without restart.
- **Pros**: Easier iterative tweaking (just edit file); can include per-skin metadata (labels) for frontend menus.
- **Cons**: Need file watcher / caching logic; more moving parts; editing file incorrectly could break serving mid-flight.

## Option C – Database-stored skin preference with admin UI
- **Approach**: Extend settings tables to record available skins/default and build a small admin form to flip between them.
- **Pros**: Changes propagate immediately through the UI; auditable in DB.
- **Cons**: Requires auth UI work + DB schema changes; heavier than needed for operator-level config; more coordination with future admin features.

## Recommendation
Adopt **Option A** for this capability. Environment variables/settings already drive most operator configuration, and reading the manifest at startup is straightforward. We can document the rebuild + restart flow and later add UI niceties if desired.
