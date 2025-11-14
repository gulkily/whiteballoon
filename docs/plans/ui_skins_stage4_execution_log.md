# UI Skins — Stage 4 Execution Log

| Date | Capability/Task | Code References | Tests / Verification | Open Risks |
| --- | --- | --- | --- | --- |
| 2025-11-14 | C1 (token inventory + base extraction + default bundle) | `static/skins/base.css`, `static/skins/default.css`, `templates/base.html`, `docs/skins/token_inventory.md` | Manual CSS spot-check, `./wb version` (CLI) | Still need to convert remaining literal RGBA values into semantic tokens before Terminal/Win95 skins. |
| 2025-11-14 | C2 (multi-bundle builder) | `tools/skins_build.py`, `tools/dev.py`, `wb.py`, `docs/skins/token_inventory.md`, `.gitignore` | `./wb skins build --dry-run`, `./wb skins build`, manual watch invocation | Need to integrate manifest consumption + admin config in C3; watch mode uses polling (could upgrade to watchdog later). |
| 2025-11-14 | C3 (config + serving) | `app/config.py`, `app/skins/runtime.py`, `app/routes/ui/helpers.py`, `app/hub/app.py`, `app/hub/admin.py`, `templates/base.html`, `docs/skins/token_inventory.md` | `./wb skins build --dry-run`, `./wb version` | Requires future UI selector (C4) to let users switch skins client-side; preview param disabled unless env flag set. |
| 2025-11-14 | Terminal skin bundle | `static/skins/terminal.css`, `docs/skins/token_inventory.md` | `./wb skins build` | Need frontend selector (C4) to expose it; operators must add `terminal` to `WB_SKINS_ALLOWED`. |
