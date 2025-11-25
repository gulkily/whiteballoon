# Mobile Navigation & Typography Simplification — Step 3 Development Plan

1. **Stage 1: Responsive Nav Container**
   - Add utility classes/breakpoint checks to wrap nav content in a mobile container.
   - Introduce a compact pill/drawer trigger that displays username + role chip; hide redundant inline badges on ≤768px.
   - Verification: manual check of header overflow and focus order.

2. **Stage 2: Drawer / Expanded Panel**
   - Implement a simple disclosure panel (no frameworks) for role badges + theme toggle.
   - Ensure ESC key / outside click closes panel; manage ARIA attributes.
   - Verification: manual keyboard navigation and VoiceOver/NVDA spot check.

3. **Stage 3: Typography Token Adjustments**
   - Update CSS custom properties for font sizes/padding at mobile breakpoints (headings, buttons, chips).
   - Confirm adjustments propagate to detail/feed pages without regressing desktop sizing.
   - Verification: manual visual inspection on 320px–768px widths.

4. **Stage 4: QA & Documentation**
   - Smoke test across dark/light themes, ensuring nav toggle persists state appropriately.
   - Document the new mobile nav behaviour in README or design notes.
   - No automated tests required per process.
