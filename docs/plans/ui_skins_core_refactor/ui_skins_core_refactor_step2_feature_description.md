# UI Skins Core Refactor — Step 2 Feature Description

## Problem
`static/css/app.css` mixes global layout utilities, component styles, and the default skin’s colors/typography. This coupling makes it hard to introduce additional skins (Terminal, Win95) without duplicating CSS or risking regressions. We need a clean separation between base styles and skin-specific overrides.

## User Stories
- **Instance operator**: wants the existing UI to remain pixel-identical while foundational refactoring occurs so current deployments remain stable.
- **Frontend developer**: wants a clearly defined base stylesheet that every skin can extend, reducing the effort to craft new looks.
- **Designer**: wants documented tokens (colors, borders, typography) so they can specify new skins without touching low-level CSS.

## Core Requirements
- Create a shared `skins/base.css` (or similar) containing layout primitives, typography scales, spacing utilities, and neutral component scaffolding (no brand colors).
- Refactor the current default styling into `skins/default.css` that imports the base partial and applies brand-specific tokens.
- Replace hard-coded colors/typography references across components with token-based variables defined in the default skin.
- Provide tooling or documentation explaining the token set so future skins know which variables to override.
- Ensure the compiled output for the default skin matches the previous single `app.css` visually and semantically.

## User Flow
1. Developer runs the build (or dev server); it generates `skin-base.css` (intermediate) and `skin-default.css` (served to clients).
2. Base template links only the default bundle; users see no change.
3. Developers creating new skins import `skins/base.css` and override tokens in their own bundle entrypoint.

## Success Criteria
- Spot-check pages show no visual regression compared to pre-refactor builds.
- CSS build emits `skin-default.css` (plus base partial) without increasing total size by more than ~5%.
- Documentation lists the exported token names and guidance for extending skins.
