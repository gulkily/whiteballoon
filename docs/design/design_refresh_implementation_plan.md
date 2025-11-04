# Design Refresh Implementation Plan

## Step 1: Palette & CSS Variable Setup
- Update light/dark theme CSS variables with new lavender/aqua palette.
- Introduce extra variables for bubble highlights, nav backgrounds, stat pills.
- Document changes in CSS comments for maintainability.

## Step 2: Animated Background Layer
- Implement gradient animation (CSS keyframes) with `prefers-reduced-motion` guard.
- Add floating bubble elements via reusable CSS classes.
- Provide optional JS toggle to pause motion (if time permits).

## Step 3: Navigation & Hero Enhancements
- Convert nav to glassmorphism style; reposition “Send Welcome” CTA into hero.
- Add community stat badges/rotating snippets in hero section.
- Integrate trending category pills below hero copy.

## Step 4: Request Card & Badge Styling
- Lighten card backgrounds; add avatar/bubble icon next to usernames.
- Update status badges with gradient rings, microcopy (e.g., “awaiting responders”).
- Adjust completed/open ghost states for contrast.

## Step 5: Button & Interaction Polish
- Enhance button gradients/shimmer (done) and ensure consistent icon usage.
- Add small icons to CTAs (e.g., sparkle for “Share request”).
- Review hover/focus states for accessibility.

## Step 6: Accessibility & Motion Review
- Verify color contrast using manual/automated tools.
- Double-check `prefers-reduced-motion` handling for all animation layers.
- Ensure new elements are keyboard navigable (e.g., trending pills, stat badges).

## Step 7: QA & Documentation
- Perform manual testing on desktop/mobile (light/dark, reduced motion).
- Update README/cheatsheet with summary of new design cues.
- Gather feedback from stakeholders and iterate if needed.
