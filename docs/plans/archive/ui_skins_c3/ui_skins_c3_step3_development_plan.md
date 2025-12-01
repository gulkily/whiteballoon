# UI Skins C3 (Config & Serving) — Step 3 Development Plan

## Stage 1 – Settings + manifest loader
- **Goal**: Define configuration knobs and write a helper that loads the skin manifest.
- **Changes**: Add env settings (allowed/default/manifest path, preview flag) to `app/config`. Implement a function (e.g., `load_skin_manifest()`) that reads JSON, validates required skins, and returns structured data.
- **Verification**: Unit-ish test via REPL or simple script to ensure manifest parsing works and errors are raised for missing skins.
- **Risks**: Manifest may not exist in dev until builder runs; need sensible defaults/fallback.

## Stage 2 – Template/context wiring
- **Goal**: Make templates consume the manifest-driven data.
- **Changes**: Expose `skins_context` via template globals or request state (perhaps in `app/routes/ui/helpers.py`). Update `templates/base.html` to reference the resolved default bundle URL (including hash). Provide optional query-param override when preview flag is set.
- **Verification**: Run dev server; confirm `<link>` uses hashed filename after `./wb skins build`. Test missing manifest scenario falls back gracefully.
- **Risks**: Hash filenames change often; ensure caching headers don’t break. Need to consider static files served directly by ASGI/Uvicorn.

## Stage 3 – Logging/documentation
- **Goal**: Ensure operators know how to configure and troubleshoot.
- **Changes**: Update `docs/skins/token_inventory.md` or new doc with env var instructions; mention preview flag and manifest path. Add startup logs summarizing which skins are enabled. Optionally add CLI `./wb skins status` (stretch) to print manifest summary.
- **Verification**: Review docs; run `./wb runserver` to see log output.
- **Risks**: None major; just keep docs accurate.
