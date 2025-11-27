# Request Detail Page Polish — Step 3 Development Plan

1. **Stage 1: Hero Layout & Metadata Strip**
   - Adjust template to split hero into back link row + title/metadata row.
   - Add metadata chunk (requester, status badge, friendly timestamp) with responsive alignment.
   - Update CSS tokens for spacing and mobile stacking.
   - Verification: manual desktop + mobile checks.

2. **Stage 2: Share Widget Refresh**
   - Replace existing input style with full-width pill, copy icon, and inline “Copied!” state.
   - Extend current JS to show temporary feedback (no external libs).
   - Ensure focus/keyboard accessibility.
   - Verification: manual copy interaction on desktop/mobile.

3. **Stage 3: Card Depth & Footer Block**
   - Lighten request card background (glass blur/inner glow) and adjust padding.
   - Introduce footer section for “Next steps” placeholder (e.g., contact email, coming-soon note).
   - Sync styles with responsive layout tokens.
   - Verification: manual READ view in dark/light themes.

4. **Stage 4: QA & Documentation**
   - Smoke test entire page desktop/mobile; ensure auto-copy still works.
   - Update README or design notes if behaviour changed.
   - Document summary in Step 4 file; no automated tests per process update.
