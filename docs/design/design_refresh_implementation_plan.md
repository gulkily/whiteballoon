# Design Refresh Implementation Plan

## Step 1: Palette & CSS Variable Setup
- Update light/dark theme CSS variables with new lavender/aqua palette.
- Introduce extra variables for bubble highlights, nav backgrounds, stat pills.
- Document changes in CSS comments for maintainability.

## Step 2: Animated Background Layer
- Implement gradient animation (CSS keyframes) with `prefers-reduced-motion` guard.
- Add floating bubble elements via reusable CSS classes.
- Provide optional JS toggle to pause motion (if time permits).

## Step 3: Navigation & Hero Styling
- Apply glassmorphism styling to nav (transparent, blurred background).
- Refine hero typography, add soft glow, and ensure heading/subheading reflect mutual-aid tone.
- Introduce optional subtle iconography (hands, hearts) without altering layout.

## Step 4: Request Card & Badge Styling
- Lighten card backgrounds and borders to align with new palette.
- Refresh status badges with gradient rings, gentle shimmer, and accessible contrast.
- (Optional) Add decorative bubble icon via CSS pseudo-element (no layout change).

## Step 5: Button & Interaction Polish
- Enhance button gradients/shimmer (completed) and confirm consistent styling across components.
- Review hover/focus states for accessibility and coherence.

## Step 6: Accessibility & Motion Review
- Verify color contrast using manual/automated tools.
- Double-check `prefers-reduced-motion` handling for all animation layers.
- Ensure new elements are keyboard navigable (e.g., trending pills, stat badges).

## Step 7: QA & Documentation
- Perform manual testing on desktop/mobile (light/dark, reduced motion).
- Update README/cheatsheet with summary of new design cues.
- Gather feedback from stakeholders and iterate if needed.
