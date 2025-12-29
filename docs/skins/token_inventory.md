# Skinning Base — Token Inventory

## File Structure
- `static/skins/base.css` — shared layout + component scaffolding every skin imports. Contains positioning, spacing, typographic scales, and references to semantic color tokens (no direct values).
- `static/skins/default.css` — the first bundle. It `@import`s `base.css`, defines all token values for light/dark, and is now linked from `templates/base.html`.
- `static/css/app.css` — legacy alias that simply `@import`s `../skins/default.css` so older references keep working during the transition.

To add another skin, create `static/skins/<name>.css`, import `./base.css`, then define token values and any extra overrides. Point your template/JS to the desired bundle once C2 (multi-bundle loader) ships.

## Global CSS Custom Properties
| Token | Purpose | Light Value | Dark Value |
| --- | --- | --- | --- |
| `--color-surface` | Page background | `#f8f5ff` | `#0f172a` |
| `--color-card` | Card surface fill | `rgba(255, 255, 255, 0.85)` | `rgba(17, 24, 39, 0.85)` |
| `--color-input` | Inputs/textareas bg | `#ffffff` | `#1f2937` |
| `--color-text` | Primary body text | `#10172a` | `#e2e8f0` |
| `--color-muted` | Secondary text | `#707a95` | `#c3d0ff` |
| `--color-accent` | Accent foreground | `#7c3aed` | `#c084fc` |
| `--color-accent-strong` | Hover/active accent | `#6d28d9` | `#a855f7` |
| `--color-border` | Card/input borders | `rgba(124, 58, 237, 0.25)` | `rgba(192, 132, 252, 0.35)` |
| `--color-success` | Success states | `#22c55e` | `#4ade80` |
| `--color-warning` | Warning states | `#d97706` | `#facc15` |
| `--color-danger` | Danger states | `#dc2626` | `#f87171` |
| `--color-info` | Info states | `#38bdf8` | `#38bdf8` |
| `--color-warm` | Gradient/badge accent | `#fb7185` | `#fb7185` |
| `--color-bubble-highlight` | Hero gradient highlight | `rgba(244, 114, 182, 0.4)` | `rgba(236, 72, 153, 0.35)` |
| `--color-bubble-cool` | Hero gradient cool accent | `rgba(129, 140, 248, 0.45)` | `rgba(129, 140, 248, 0.4)` |
| `--color-hero-glow` | Glow behind cards | `rgba(192, 132, 252, 0.25)` | `rgba(76, 29, 149, 0.35)` |
| `--shadow-sm` | Button/card hover shadow | `0 1px 2px rgba(15, 23, 42, 0.08)` | `0 1px 2px rgba(15, 23, 42, 0.4)` |
| `--shadow-md` | Elevated card shadow | `0 14px 40px rgba(124, 58, 237, 0.2)` | `0 14px 40px rgba(76, 29, 149, 0.45)` |
| `--gap-sm`, `--space-*`, `--radius-*`, `--font-*`, `--line-height-*` | Layout, typography, spacing | as defined | (same in dark) |

## Skin-Specific Tokens (new)
| Token | Description | Light Default | Dark Default |
| --- | --- | --- | --- |
| `--color-on-accent` | Text/icon color when placed on accent backgrounds | `#ffffff` | `#ffffff` |
| `--skin-account-role-bg` | Background for "role" badges | `rgba(100, 116, 139, 0.18)` | same |
| `--skin-account-role-text` | Text color for role badges | `var(--color-muted)` | `var(--color-muted)` |
| `--skin-account-admin-bg` | Background for admin badges | `rgba(37, 99, 235, 0.12)` | same |
| `--skin-account-admin-text` | Text color for admin badges | `var(--color-accent)` | `var(--color-accent)` |
| `--skin-account-half-bg` | Background for half-auth badges | `rgba(217, 119, 6, 0.14)` | same |
| `--skin-account-half-text` | Text color for half-auth badges | `#b45309` | `#b45309` |
| `--skin-account-ok-bg` | Background for ok badges | `rgba(21, 128, 61, 0.14)` | same |
| `--skin-account-muted-bg` | Background for muted badges | `rgba(100, 116, 139, 0.16)` | same |
| `--skin-theme-toggle-border` | Theme toggle border color | `rgba(124, 58, 237, 0.35)` | `rgba(96, 165, 250, 0.35)` |
| `--skin-theme-toggle-bg` | Theme toggle background | `rgba(124, 58, 237, 0.15)` | `rgba(96, 165, 250, 0.18)` |
| `--skin-theme-toggle-foreground` | Theme toggle icon color | `var(--color-accent)` | `#bfdbfe` |
| `--skin-theme-toggle-auto-border` | Border for auto mode indicator | `rgba(124, 58, 237, 0.75)` | `rgba(191, 219, 254, 0.85)` |
| `--skin-theme-toggle-auto-bg` | Background for auto mode indicator | `rgba(124, 58, 237, 0.22)` | `rgba(147, 197, 253, 0.2)` |
| `--skin-background-gradient` | Hero background gradient stack | see default definition | dark variant per default |
| `--skin-bubble-background` | Bubble gradient fill | see default definition | dark variant per default |
| `--skin-bubble-shadow` | Bubble drop shadow | `0 0 25px rgba(124, 58, 237, 0.25)` | `0 0 25px rgba(99, 102, 241, 0.2)` |

Future skins override these tokens (and may add new ones). Keeping them grouped here helps track coverage.

## Gaps / Decisions Needed
1. Define semantic tokens for status pills (e.g., `--color-status-success-bg`, `--color-status-danger-text`).
2. Determine whether gradients remain part of base or move into skin-specific overrides.
3. Clarify typography tokens for retro skins (Win95) that may alter fonts.

## Workflow Cheat Sheet
1. When adding a new component, pull layout styles into `base.css` but keep colors referencing tokens.
2. Update `docs/skins/token_inventory.md` with any new token names/semantics.
3. For experimental skins, copy `static/skins/default.css` → `static/skins/<variant>.css`, tweak token values, and add overrides beneath the import.

## Building Skin Bundles (C2)
- Run `./wb skins list` to see all discovered `static/skins/*.css` entries without touching the build outputs.
- Run `./wb skins build` to compile every `static/skins/*.css` (excluding `base.css`) into hashed bundles under `static/build/skins/` and emit `manifest.json`.
- Use `./wb skins build --dry-run` to list available skins without writing files.
- During development, `./wb skins watch` rebuilds on changes (polling every second by default). Stop with `Ctrl-C`.
- CI/release checklist: execute `./wb skins build` so bundles + manifest are up to date before packaging artifacts.

## Configuring Skins in the App (C3)
- `WB_SKINS_ENABLED` (default `false`): master switch for manifest-driven skins. When `false`, the app loads `/static/skins/default.css` directly.
- `WB_SKIN_DEFAULT` (default `default`): slug of the bundle that should load by default.
- `WB_SKINS_ALLOWED`: comma-separated list of skins operators are willing to expose (default falls back to the default skin). The default skin is automatically added if missing.
- `WB_SKINS_MANIFEST_PATH` (default `static/build/skins/manifest.json`): filesystem path to the build manifest produced by `./wb skins build`.
- `WB_SKIN_PREVIEW_ENABLED` (default `false`): when `true`, requests may pass `?skin=<name>` (param configurable via `WB_SKIN_PREVIEW_PARAM`, default `skin`) to preview another allowed skin without changing global config.
- `WB_SKIN_STRICT` (default `false`): when `true`, the app raises an error if the configured skin is missing from the manifest. Otherwise it falls back to `/static/skins/<name>.css` and logs a warning.

Remember to restart the app after changing these values so `get_settings()` reloads the configuration.

## Bundled Skins
- **default** – current brand palette with gradient background.
- **terminal** – retro green-on-black terminal aesthetic (monospace fonts, neon accents). Enable via `WB_SKINS_ALLOWED=default,terminal` and `WB_SKIN_DEFAULT=terminal` if desired.
- **paper** – notebook-inspired cream palette with handwritten fonts and dotted-grid background. Enable via `WB_SKINS_ALLOWED=default,paper`.
- **signal-ledger** – investor-grade deep navy theme with copper + teal accents, serif headings, KPI hero row, and horizontal timeline strip. Enable via `WB_SKINS_ALLOWED=default,terminal,paper,signal-ledger` and preview with `?skin=signal-ledger` when preview mode is on.
- **break-in** – neon night-mode hero with glowing CTAs and blurred Bay Bridge photography inspired by the Break In event page. Enable via `WB_SKINS_ALLOWED=default,terminal,paper,signal-ledger,break-in` (and optionally `?skin=break-in` while preview mode is toggled on) to get the electric lime typography, glass buttons, and skyline hero treatment.
