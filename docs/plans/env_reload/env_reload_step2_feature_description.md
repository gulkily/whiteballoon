# Env Reload Step 2: Feature Description

Problem: The dev server reloads when `.env` changes, but updated values do not apply because the reloaded process keeps stale environment state.

User stories:
- As a developer, I want edits to `.env` to take effect after the auto-reload so that I can iterate without full restarts.
- As an administrator, I want `.env`-backed feature toggles to reflect my latest changes so that the UI matches intended configuration.
- As an operator, I want the runtime configuration to be predictable after reload so that debugging relies on current settings.

Core requirements:
- After an auto-reload triggered by `.env` changes, the runtime uses the updated `.env` values.
- Updated `.env` values take precedence over stale inherited environment values for the running dev server.
- Configuration reads during requests reflect the latest `.env` values after reload.
- Behavior remains unchanged when `.env` is missing or unchanged.

Shared component inventory:
- `app/env.py` (env loader): reuse and extend to ensure updated values are applied after reload.
- `app/config.py` settings access: reuse and extend so cached settings align with updated environment values.
- `tools/dev.py` `runserver` reload watch: reuse; continue relying on `.env` file watching.
- `app/routes/ui/admin.py` `.env` update surfaces (messaging + Dedalus): reuse; no new UI required.
- `app/routes/ui/helpers.py` template globals: reuse; continue pulling from shared settings.

Simple user flow:
1. Developer edits `.env` while the dev server is running.
2. The server reloads automatically.
3. The reloaded process applies the updated environment values.
4. Pages and features reflect the new configuration without a manual restart.

Success criteria:
- Editing `.env` and triggering a reload results in observable changes (e.g., toggles, titles, feature flags) on the next request.
- No manual server restart is required to pick up `.env` updates during development.
- Configuration values remain consistent with `.env` across multiple reload cycles.
