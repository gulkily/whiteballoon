## Stage 1 – Override .env on load
- Changes: Updated env loader to call `load_dotenv(override=True)` so reloads apply the latest `.env` values.
- Verification: Not run (per project guidance). Manual check: edit `.env` (e.g., `SITE_TITLE`), wait for reload, refresh UI to confirm new value.
- Notes: Prioritizes `.env` over inherited environment values during dev reloads.

## Stage 2 – Settings cache alignment
- Changes: No additional code required; settings are rebuilt in the reloaded process once `.env` overrides apply.
- Verification: Not run (per project guidance). Manual check: change a feature flag in `.env`, reload, confirm templates reflect the new value.
- Notes: Reload already spawns a fresh process, so cached settings do not persist across reloads.

## Stage 3 – Admin .env updates alignment
- Changes: No additional code required; admin env writers already update `os.environ` and reset the settings cache.
- Verification: Not run (per project guidance). Manual check: toggle messaging or update Dedalus key in admin UI, confirm UI reflects new state.
- Notes: Admin routes call `config.reset_settings_cache()` after updates.
