# Feed Spacing & Card Hierarchy Refresh — Step 3 Development Plan

1. **Stage 1: Rhythm Tokens & Section Spacing**
   - Introduce CSS utilities/variables for vertical rhythm (section gaps, card margins).
   - Apply to feed hero, requests list, and pending sections.
   - Verification: manual desktop/mobile check for consistent spacing.

2. **Stage 2: Card Meta Strip Alignment**
   - Update request card header to align requester, status badge, and timestamp horizontally.
   - Ensure timestamp link styling matches detail page; adjust badge sizing if needed.
   - Verification: manual scan of feed + detail view to confirm parity.

3. **Stage 3: Action Hierarchy Updates**
   - Restyle primary and secondary buttons in hero and card footers (color, hover states) to clarify priority.
   - Confirm disabled/readonly states inherit correctly.
   - Verification: manual interaction check in light/dark themes.

4. **Stage 4: QA & Documentation**
   - Smoke test feed (desktop/mobile) with mix of open/completed/pending requests.
   - Update design notes if new spacing tokens or button guidelines are introduced.
   - No automated tests required per process.
