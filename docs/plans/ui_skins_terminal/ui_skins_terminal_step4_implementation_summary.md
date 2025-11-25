# Terminal Skin — Implementation Summary

- Added `static/skins/terminal.css` importing `base.css` and redefining tokens for a phosphor-green terminal aesthetic (monospace fonts, neon accents, adjusted gradients/shadows).
- Documented the new skin under "Bundled Skins" in `docs/skins/token_inventory.md` so operators know how to enable it.
- Ran `./wb skins build` to generate the hashed bundle (`skin-terminal.<hash>.css`) and update the manifest.

Next steps: include "terminal" in `WB_SKINS_ALLOWED` and optionally set `WB_SKIN_DEFAULT=terminal` to preview the look until the selector (C4) ships.
