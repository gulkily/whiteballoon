# Font Refresh — Step 3 Development Plan

1. **Stage 1: Font selection & asset prep**
   - Choose two open-source fonts (display + body) with friendly, mutual-aid vibe.
   - Generate WOFF2 files (regular, medium, bold weights) and place in `static/fonts/`.

2. **Stage 2: CSS `@font-face` and variable updates**
   - Add `@font-face` declarations to CSS (with local fallbacks, `font-display: swap`).
   - Update root font stacks for headings/body.

3. **Stage 3: Typography scale adjustments**
   - Tweak heading sizes, line heights, letter spacing to match new fonts.
   - Ensure components (buttons, badges) adapt without layout shifts.

4. **Stage 4: Accessibility & performance checks**
   - Confirm contrast with new weights; verify no external font requests.
   - Test on mobile/desktop; ensure fallback behavior.

5. **Stage 5: QA & documentation**
   - Run `pytest`; manual visual QA.
   - Document font sources and usage in README/cheatsheet.
