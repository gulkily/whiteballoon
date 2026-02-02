# Step 3: Development Plan — /llms.txt for running instance

1) Stage 1 — Inventory canonical data sources
- Goal: Identify which settings, routes, and feature toggles should populate `/llms.txt` and where they live today.
- Dependencies: `app/config.py` settings, `.env` / `.env.example`, existing docs (`README.md`, `docs/spec.md`).
- Expected changes: None to code; capture a short list of fields to expose (base URL, site title, feature flags, enabled modules, key public routes/APIs). Note any sensitive fields to exclude.
- Verification: Manual review of settings to confirm availability and sensitivity.
- Risks/open questions: Are there runtime-only flags not represented in `Settings`? Is there a canonical base URL helper already used in templates?
- Canonical components/API contracts: Use existing public routes from `docs/spec.md` and `README.md`.

2) Stage 2 — Add a runtime `/llms.txt` endpoint
- Goal: Serve a machine-readable text response at `/llms.txt` that reflects current configuration.
- Dependencies: FastAPI router structure in `app/routes/ui` or a dedicated minimal route module; settings access via `get_settings()`.
- Expected changes: Add a new route handler (e.g., `GET /llms.txt`) that returns `text/plain`; introduce a simple renderer function that composes the content from settings + canonical route list; avoid template usage to keep response lightweight.
- Verification: Manual `curl http://127.0.0.1:8000/llms.txt` returns 200, `text/plain`, and the expected fields.
- Risks/open questions: Ensure no secrets leak; decide which router to mount (`app/routes/ui/branding.py` or new module) without creating conflicts.
- Canonical components/API contracts: Preserve existing public endpoints and auth flows; no new API surface beyond `/llms.txt`.

3) Stage 3 — Align content with enabled feature flags
- Goal: Ensure `/llms.txt` accurately reflects toggles like messaging, skins, and peer-auth flags.
- Dependencies: Settings definitions in `app/config.py` and `.env.example`.
- Expected changes: Extend the content builder to include a concise “Features” section keyed off settings (e.g., messaging enabled/disabled, skins enabled/allowed, peer auth queue on/off).
- Verification: Toggle a setting in `.env`, restart server, confirm `/llms.txt` updates.
- Risks/open questions: Confirm boolean parsing for `WB_SKINS_ENABLED` and similar flags; decide which flags are relevant to agents.
- Canonical components/API contracts: Reflect existing feature-gated UI routes (e.g., `/messages` only if enabled).

4) Stage 4 — Documentation pointer and safety check
- Goal: Point agents to canonical docs and confirm no sensitive values are emitted.
- Dependencies: `README.md`, `docs/spec.md`.
- Expected changes: Add “Docs” section with relative paths; add explicit note that API keys and private tokens are never included.
- Verification: Manual review of output and a quick grep for secret-like fields (e.g., `*_KEY`, tokens).
- Risks/open questions: Ensure the doc links remain stable for repo users running locally.
- Canonical components/API contracts: Reference existing docs rather than creating new guidance.
