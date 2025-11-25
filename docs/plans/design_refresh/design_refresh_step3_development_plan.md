# Design Refresh — Step 3 Development Plan

1. **Stage 1: Animated background layer**
   - Add CSS gradient animation (keyframes) or minimal JS canvas overlay for moving background that evokes a collaborative, uplifting atmosphere; include `prefers-reduced-motion` guard.
   - Testing: Manual on desktop/mobile; ensure performance acceptable.

2. **Stage 2: Bubble accents & confetti details**
   - Introduce floating bubble elements (absolute-positioned divs with animation) around mutual-aid cards, headers, and calls-to-action so support feels present.
   - Testing: Visual checks, ensure no layout overlaps.

3. **Stage 3: Palette & component tweaks**
   - Update CSS variables for cards/buttons (bubble look, rainbow palette, semi-transparent layers); ensure contrast.
   - Testing: Confirm components readable; dark mode compatibility.

4. **Stage 4: Reduced-motion & accessibility safeguards**
   - Implement media queries / class toggles to disable heavy animation when `prefers-reduced-motion` true; document behavior.
   - Testing: Simulate reduced-motion setting.

5. **Stage 5: QA & documentation**
   - Run `pytest` (acknowledging empty suite); manual walkthrough; note design changes in README/cheatsheet if needed.
