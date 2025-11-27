# UI Skins C3 (Config & Serving) — Step 2 Feature Description

## Problem
Even after building hashed skin bundles, the app always serves `/static/skins/default.css`. Operators can’t flip to Terminal/Win95 skins, and the frontend has no awareness of the bundle manifest. We need a configuration layer that defines which skins are available + which is default, validates against the manifest, and injects the correct `<link>` tags / metadata into templates (and optionally allows previewing other skins).

## User Stories
- **Instance operator**: wants to set the default skin (and optionally allow a subset of skins) by editing config/env vars without touching HTML.
- **Frontend developer**: wants templates/JS to receive a manifest-driven context so future selectors (C4) can list available skins.
- **Support engineer**: wants clear error messages if a configured skin name is missing from the manifest.

## Core Requirements
- Extend settings (e.g., `WB_SKINS_ALLOWED`, `WB_SKIN_DEFAULT`, `WB_SKINS_MANIFEST_PATH`) and load them at startup.
- Add backend helper that reads the manifest JSON, verifies the configured skins exist, and exposes resolved bundle URLs + metadata (name, hash) to Jinja templates.
- Update base template to load the default skin bundle path instead of a hard-coded link. Optionally preload additional skins (disabled for now).
- Provide a preview mechanism for developers (`?skin=` param) guarded by a config flag so we can test Terminal/Win95 before exposing them to users.
- Log/raise descriptive errors when the manifest is missing or the configured skin isn’t present.

## User Flow
1. Operator runs `./wb skins build`, then sets env vars (`WB_SKINS_ALLOWED=default,terminal` and `WB_SKIN_DEFAULT=terminal`).
2. On app startup, settings loader reads the manifest, validates the set, and exposes `skins_context` (default bundle + allowed metadata) to templates.
3. Base template `<link>` references the resolved URL (with hash). If preview flag and query param are set, the request uses a different bundle for that response only.
4. If validation fails, the app logs an error and falls back to default skin (or refuses to start depending on severity).

## Success Criteria
- Template now loads the hashed default bundle via manifest context.
- Misconfigured skin names raise clear errors (and fallback to default if `WB_SKIN_STRICT=false`).
- Optional preview query param works when `WB_SKIN_PREVIEW=1`.
- Documentation outlines config keys and required build steps.
