# UI Skins — Stage 1 Architecture Brief

## Option A – CSS Variable Skin Packs (Baseline)
- **Approach**: Keep a single compiled CSS file but define per-skin variable sets (e.g., `data-skin="midnight"`). Operators enable skins by listing allowed skins in config; frontend toggles `data-skin` on `<html>`.
- **Pros**: Minimal build changes, leverages existing CSS custom properties, easy to preview. Small runtime switch cost.
- **Cons**: Requires disciplined variable coverage; components with hard-coded colors must be refactored. Limited to what CSS vars can express (no layout/layout-density shifts).
- **Risks**: Missing vars cause subtle mismatches. Need lint/check to ensure every hard-coded color migrates.

## Option B – Multi-Bundle CSS Imports (preferred)
- **Approach**: Build discrete CSS bundles per skin (e.g., `skin-default.css`, `skin-terminal.css`, `skin-win95.css`). Each bundle can extend shared base partials but override layout, icons, and component styling more aggressively. Runtime switches the `<link>` tag (or server-side template) based on selected skin; operators configure allowed skins and default.
- **Pros**: Maximum creative freedom—skins can redefine not just tokens but background textures, border radii, or even typography scales. Isolation keeps contributions clean, letting developers iterate on Terminal/Win95 looks without touching Default. Easier to ship drastically different aesthetics later.
- **Cons**: Requires build-pipeline updates (multiple PostCSS/Tailwind runs), introduces need for loader script to swap bundles, and increases bandwidth if several skins are preloaded. Switching skins dynamically can incur FOUC unless we inline minimal critical CSS.
- **Risks**: Bundle drift (components diverge between skins), cache invalidation headaches, and more surface area for regressions; must invest in documentation and snapshot testing per skin.

## Option C – Theme Plugins via Design Tokens API
- **Approach**: Define a JSON/YAML design-token schema (colors, spacing, type) stored server-side. Frontend fetches tokens and generates CSS variables at runtime (e.g., via CSS-in-JS or injected `<style>`).
- **Pros**: Highly flexible, enables admin UI for skins, future-proofs for per-user themes.
- **Cons**: Requires runtime CSS generation, token validation, and caching. Larger engineering lift.
- **Risks**: Flash of default theme if token fetch fails; more complex security surface.

## Recommendation
Adopt **Option B** (multi-bundle CSS imports). The initial requirement includes dramatically different aesthetics (“green on black terminal” and “Windows 95”), which go beyond palette tweaks. Separate bundles let us customize typography, borders, and chrome per skin while still sharing foundational utility classes. We will ship three first-party bundles:

1. **Default** — current design, compiled as `skin-default.css`.
2. **Terminal** — monochrome/green-on-black styling with CRT-inspired accents (`skin-terminal.css`).
3. **Win95** — gray panels, beveled buttons, and retro fonts reminiscent of Windows 95 (`skin-win95.css`).

Later skins can be developed by extending the build pipeline with new bundle entries.

## Open Questions
1. How will operators configure available skins? (env var vs admin UI vs file drop)
2. Do skins coexist with light/dark auto toggle (e.g., skin defines both light/dark variants) or replace it entirely?
3. What tooling ensures new components use skin-aware variables (linting, docs)?
4. How to preview skins in dev server (URL param, query, CLI flag)?
