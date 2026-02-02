## Stage 1 – Inventory canonical data sources
- Changes: Reviewed settings in `app/config.py`, routing in `app/main.py`, and canonical docs (`README.md`, `docs/spec.md`) to determine fields and public routes to expose.
- Verification: Manual review of settings + route inventory.
- Notes: Confirmed sensitive fields (e.g., API keys) must be excluded from output.

## Stage 2 – Add runtime /llms.txt endpoint
- Changes: Added a `/llms.txt` route under `app/routes/ui/misc.py` that renders a text response from live settings; mounted the misc router in `app/routes/ui/__init__.py`.
- Verification: Ran a local Python snippet to build the response via `_build_llms_text` and confirmed the header fields render.
- Notes: Output is plain text and avoids any secret-bearing settings.

## Stage 3 – Align content with enabled feature flags
- Changes: Expanded the features section to include skin preview and strictness flags from live settings.
- Verification: Generated a sample response and confirmed the new `skins_*` lines render.
- Notes: Feature list remains concise and avoids sensitive values.
