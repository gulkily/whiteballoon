# Env Reload Step 3: Development Plan

1. Goal: Ensure `.env` values override inherited environment values on app startup after reload.
   - Dependencies: `app/env.py`, `dotenv` usage.
   - Expected changes: Update env loader to call `load_dotenv(override=True)`; ensure load happens where the server process initializes.
   - Verification: Edit `.env` (e.g., `SITE_TITLE`), allow reload, confirm updated value appears in UI.
   - Risks/open questions: Override may surprise workflows that rely on shell-provided env values; confirm intended precedence is dev-focused.
   - Canonical components touched: `app/env.py`, `app/config.py` (shared settings pipeline).

2. Goal: Make settings reflect updated environment values after reload.
   - Dependencies: `app/config.py` settings cache.
   - Expected changes: Add a safe cache reset hook during app startup or reload path so settings are rebuilt from current env.
   - Verification: Toggle `ENABLE_DIRECT_MESSAGING` or `SITE_TITLE` in `.env`, reload, confirm template globals/feature flags update.
   - Risks/open questions: Ensure cache reset does not add per-request overhead; decide if reset happens only on startup.
   - Canonical components touched: `app/config.py`, `app/routes/ui/helpers.py` (template globals from settings).

3. Goal: Ensure admin `.env` updates stay aligned with runtime behavior.
   - Dependencies: `app/routes/ui/admin.py` env writes.
   - Expected changes: Confirm admin endpoints rely on shared settings flow and do not introduce separate caches; document if any explicit reset is required.
   - Verification: Update Dedalus or messaging toggle via admin UI, confirm UI and behavior update after reload.
   - Risks/open questions: If admin updates bypass reload, ensure outcome is still consistent with env loading strategy.
   - Canonical components touched: `app/routes/ui/admin.py`, `app/env.py`.
