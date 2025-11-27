# HTMX Retirement – Development Plan

1. **Inventory & UX Decision**
   - Dependencies: Feature description approved; codebase current on main.
   - Changes: Audit templates/backend for HTMX usage (attributes, script tag, partial routes); choose replacement pattern that preserves server-rendered initial page while offering enhancement (vanilla JS fetch vs. redirect).
   - Testing: Manual checklist verifying all HTMX references catalogued.
   - Risks: Missing hidden interactions; mitigate with exhaustive grep and template review.

2. **Introduce Minimal JS Helpers**
   - Dependencies: Stage 1 audit completed.
   - Changes: Add a small `static/js/requests.js` (or inline module) to handle show/hide of request form and submit/complete actions via Fetch; wire script into base template.
   - Testing: Browser smoke test for form toggle and submission; ensure JS disabled fallback (form posts normally).
   - Risks: Regressing registration flow; mitigate with manual test of signup + first request.

3. **Update Templates & Routes**
   - Dependencies: Stage 2 helpers ready.
   - Changes: Remove HTMX attributes and partial routes; adjust `/requests` endpoints/templates to keep initial loads server-rendered and support enhancement via standard POST/redirect plus JSON paths.
   - Testing: Demo flows in browser (create/complete request, cancel form); ensure login-required messaging still appears.
   - Risks: 404s from deleted partial endpoints; mitigate by updating all links/buttons in same stage.

4. **Cleanup & Docs**
   - Dependencies: Stage 3 behaviour confirmed.
   - Changes: Delete HTMX script tag, dependency references, and unused templates; update README/cheatsheet to mention new JS helper.
   - Testing: `git grep htmx` should return nothing; run `pytest --collect-only` (if available) to confirm imports.
   - Risks: Lingering assets or docs; mitigate with final grep and doc review.
