# Background & Motion Finishing Pass — Step 3 Development Plan

1. **Stage 1: Token Audit & Base Gradient**
   - Extract gradient color stops/opacities into shared CSS variables.
   - Apply updated tokens to global background and hero sections.
   - Verification: manual desktop check for contrast and banding.

2. **Stage 2: Bubble Layout & Animation Cadence**
   - Rebalance bubble sizes/positions; standardize animation duration/easing.
   - Ensure reduced-motion removes animation but keeps layout pleasant.
   - Verification: manual scroll + reduced-motion test.

3. **Stage 3: Page-specific Adjustments**
   - Reapply tokens to detail and invite surfaces, tuning opacity for overlays.
   - Confirm card shadows and gradients stay harmonious.
   - Verification: manual comparison across main pages.

4. **Stage 4: QA & Documentation**
   - Smoke test light/dark themes, large monitors, and mobile viewports.
   - Document the new tokens and motion guidelines in design notes.
   - No automated tests planned.
