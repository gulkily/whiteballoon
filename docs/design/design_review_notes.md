# Design Review Notes — Mutual-Aid Bubbly Theme

## Narrative & Layout
- Replace the plain hero copy with community storytelling, e.g., “Neighbors asking for a lift today.”
- Add subcopy highlighting mutual aid: recent activity counters, rotating “recently helped” snippets.
- Alternate background bubbles behind request cards to suggest asker/helper pairs.
- Introduce small stat badges in hero (“123 neighbors helped this month”).

## Cards & Typography
- Lighten card background (rgba(12, 18, 38, 0.8)) for readability.
- Increase base font size and line height; lighten timestamps.
- Add avatar initials or bubble icons near usernames.
- Consider subtle texture overlay behind cards to separate them from the gradient.

## Buttons & Badges
- Keep gradient buttons but add small icons (sparkle/heart/hand) to underline warmth.
- Soften hover: glow vs. large lift; reduce shadow intensity.
- Status badges: gradient ring, subtle shimmer, tooltips (“awaiting responders”, “completed by three neighbors”).

## Navigation
- Shrink the “Dark” toggle to icon-only, move far right.
- Move “Send Welcome” call-to-action into hero area or highlight as special bubble.
- Retain glass blur but lighten nav background for readability.

## Contrast & Motion
- Ensure `prefers-reduced-motion` disables gradient/bubble animation.
- Optional: add manual “Pause background motion” toggle.
- Add soft diagonal texture overlay to avoid banding on widescreen.

## Community Cues
- Add “Neighbors helped in the last 24h” bubble avatars near hero.
- Display trending categories (Groceries, Rides, Tech Support) as pill links.
- Show supportive microcopy under status badges.

## Implementation Notes
- No new dependencies—pure CSS/HTML/vanilla JS.
- Expand CSS variables for new palette (lavender/aqua/peach highlights).
- Use `mix-blend-mode`, `filter`, and gradients to style bubble edges and shimmer.
