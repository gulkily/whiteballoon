# Env Reload Step 1: Solution Assessment

Problem statement: The dev server reloads when `.env` changes, but updated environment values do not take effect at runtime.

## Option A: Override `.env` values on startup and refresh settings cache on reload
- Pros: Minimal change, keeps reload workflow intact, ensures new values win over inherited process env.
- Cons: Overrides shell-provided env values, could surprise production workflows if not scoped.

## Option B: Move `.env` loading to the server process only (or clear inherited `.env` values before reload)
- Pros: Preserves external env precedence, reduces override risk in production.
- Cons: Touches CLI bootstrap flow, more coordination between reloader and server process.

## Option C: Add explicit runtime env reload (manual action or file watcher)
- Pros: Lets operators refresh settings without full restart, clear control surface.
- Cons: Higher complexity, risk of mid-request config drift, additional behavior to document.

Recommendation: Option A. It targets the root cause (inherited env values + cached settings) with the smallest change while preserving current developer workflows.
