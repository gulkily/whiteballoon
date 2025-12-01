# Dark Mode Support — Step 3 Development Plan

1. **Stage 1: Dark palette + CSS variable audit**
   - Dependencies: Existing `static/css/app.css` variable definitions.
   - Changes: Extend root variables with dark equivalents (e.g., `--color-card-dark`) or reassign within `[data-theme="dark"]`; ensure all UI colors reference variables.
   - Testing: Manual visual diff; run contrast checks on key components.
   - Risks: Missing variable usages leading to inconsistent theming; contrast regressions.

2. **Stage 2: Auto-detect theme bootstrap**
   - Dependencies: Stage 1 variables in place.
   - Changes: Add minimal inline script to read stored preference and/or `prefers-color-scheme`, set `data-theme` on `document.documentElement` before main CSS; ensure no FOUC.
   - Testing: Manual browser check with/without stored preference; verify auto-detect on system dark/light.
   - Risks: Script ordering causing flash; older browsers lacking support.

3. **Stage 3: Manual toggle UI + persistence**
   - Dependencies: Stage 2 bootstrap.
   - Changes: Add toggle control to header/account menu; wire small JS module to switch themes, update `localStorage`, and handle “auto” mode resetting to system preference.
   - Testing: Manual toggle interactions, persistence across reloads, mobile UX; optionally add smoke test to JS bundle.
   - Risks: Toggle placement cluttering UI; persistence bugs causing wrong theme.

4. **Stage 4: QA + documentation**
   - Dependencies: Stages 1-3 complete.
   - Changes: Cross-browser QA (desktop/mobile), note contrast verification results, document toggle behavior (including auto/manual precedence).
   - Testing: Manual; update Step 4 summary doc.
   - Risks: Missing components unaffected by theming; documentation drift if future UI changes move toggle.
