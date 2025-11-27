# UI Skins — Stage 2 Capability Map

| Capability | Scope | Dependencies | Acceptance Tests |
| --- | --- | --- | --- |
| C1. Core Style Extraction | Identify shared base styles vs skin-specific layers; refactor build so utilities/layout live in `skin-base.css` partial consumed by every bundle. | None | Building `skin-default.css` from new pipeline reproduces current UI pixel-for-pixel. |
| C2. Multi-Bundle Build System | Extend CSS toolchain (e.g., PostCSS/Tailwind) to emit `skin-<name>.css` bundles, each importing base plus overrides; add watcher support for dev server. | C1 | Running `npm run build-css` (or equivalent) outputs `skin-default.css`, `skin-terminal.css`, `skin-win95.css` with hashed filenames for prod. |
| C3. Operator Configuration & Serving | Introduce config (env or JSON) listing allowed skins + default; server/template determines which `<link>` tags to render and exposes skin metadata to frontend. | C2 | Setting `WB_SKINS=default,terminal,win95` serves respective bundles; invalid skin logs warning and falls back to default. |
| C4. Frontend Skin Selector & Loader | Build UI control (desktop + mobile) to switch skins, update stored preference, and swap `<link>` element without full reload; ensure graceful fallback with JS disabled. | C3 | User toggles between Default/Terminal/Win95 without page reload; reload honors last selection; auto/dark-light toggle behavior defined per skin. |
| C5. Skin Authoring Toolkit | Provide scaffolding/docs for new skins (e.g., `./wb skin create myskin`), preview flags (`?skin=`), and lint/tests to catch missing overrides. | C4 | Developer can generate new skin skeleton, run dev server, and preview via CLI or query param; documentation outlines required files and testing checklist. |

## Dependency Graph
C1 → C2 → C3 → C4 → C5 (linear: base extraction enables multi-bundle build, which feeds config, then UI selector, then developer tooling).

## Additional Notes
- Terminal and Win95 skins live in `static/skins/terminal/` and `static/skins/win95/` directories with their own PostCSS entrypoints extending the base partial.
- Consider lazy-loading non-default skins to minimize initial payload; acceptance tests should confirm FOUC is avoided when switching at runtime (maybe inline critical CSS).
