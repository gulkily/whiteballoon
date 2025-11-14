# UI Skins Core Refactor — Step 3 Development Plan

## Stage 1 – Map existing tokens
- **Goal**: Catalog all colors, typography, and spacing constants in `static/css/app.css`.
- **Changes**: Annotate a spreadsheet or markdown table listing token names → current values; identify gaps/hard-coded values.
- **Verification**: Peer review of the token map; ensure 100% coverage of color variables.
- **Risks**: Missing hidden selectors/components leading to regressions later.

## Stage 2 – Extract base stylesheet
- **Goal**: Create `static/skins/base.css` (and optional partials) that contain layout utilities, typography scales, neutral component shells.
- **Changes**: Move relevant sections from `app.css` into base; introduce CSS variables referencing tokens (e.g., `--skin-surface`, `--skin-text`), but keep default values for now.
- **Verification**: Build default skin and confirm CSS compiles; run lint/build.
- **Risks**: Incorrect import order causing specificity issues or missing styles.

## Stage 3 – Create default skin bundle
- **Goal**: Produce `static/skins/default.css` that imports base and sets the actual brand colors/variants.
- **Changes**: Define token values (CSS variables) for default skin; ensure component selectors now reference tokens (no literals). Update template/build to load `skin-default.css` instead of `app.css`.
- **Verification**: Manual visual regression on representative screens; measure CSS bundle size (<5% growth). Add unit snapshot if available.
- **Risks**: Missed overrides leading to broken colors/contrast.

## Stage 4 – Document tokens & developer workflow
- **Goal**: Document token names, file structure, and steps for creating a new skin.
- **Changes**: Update `docs/` (e.g., `docs/skins.md`) detailing base/default layout, tokens, and how to add new bundle entrypoints. Add comments in CSS where appropriate.
- **Verification**: Walk through docs by creating a sample stub skin; ensure instructions accurate.
- **Risks**: Documentation lagging behind actual structure.

## Verification & Rollout
- After each stage, run `npm run build` (or equivalent) and `./wb runserver` smoke tests.
- Keep feature behind branch until the default skin matches production; no user-visible changes until skin selector work (later capability) lands.
