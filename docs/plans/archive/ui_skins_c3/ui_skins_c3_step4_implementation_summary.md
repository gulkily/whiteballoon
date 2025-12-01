# UI Skins C3 (Config & Serving) — Step 4 Implementation Summary

## Work Completed
1. **Settings & manifest loader**: Extended `app/config.Settings` with env-driven knobs (`WB_SKINS_ENABLED`, `WB_SKIN_DEFAULT`, `WB_SKINS_ALLOWED`, manifest path, preview flags, strict mode). Added `app/skins/runtime.py` with helpers to read the builder manifest, normalize allowed skins, and compute bundle URLs (with graceful fallbacks plus strict-mode enforcement).
2. **Template wiring**: Registered a new `skin_bundle_href(request)` Jinja global across UI + hub templates, and updated `templates/base.html` to load the resolved bundle URL instead of the hard-coded `/static/skins/default.css`. Preview overrides (query param) are honored only when the preview flag is enabled.
3. **Documentation/logging**: Documented the new env vars + workflow in `docs/skins/token_inventory.md` and logged the C3 work in the execution log.

## Verification
- `./wb skins build --dry-run` to ensure the builder still lists skins.
- `./wb version` to exercise the CLI after the config changes.
- Manual spot-check: when `WB_SKINS_ENABLED` is false, the template falls back to `/static/skins/default.css`; when true (with manifest present) it references the hashed bundle from `static/build/skins/`.

## Follow-Ups
- C4 will surface the allowed skins to the frontend toggle so users can switch without env edits.
- Consider optional watchdog-based watcher for faster rebuild feedback.
