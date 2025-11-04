# Design Follow-up Tickets — November 2025

## Ticket 1 — Request Detail Page Polish
- **Goal**: Refine `/requests/<id>` layout so it feels like a dedicated detail surface rather than a stretched feed card.
- **Scope**:
  - Split hero into two rows: text-link back affordance, then title + compact metadata (status, requester, timestamp).
  - Restyle share widget as a full-width pill with copy icon and inline “Copied!” hint; keep auto-select behaviour.
  - Lighten the request card background (glass blur/inner glow) to reintroduce depth on both desktop and mobile.
  - Add footer block for “Next steps” (contact info/CTA placeholder) to signal future tracking features.
- **Out of scope**: global nav changes, feed styling, new backend data.

## Ticket 2 — Mobile Navigation & Typography Simplification
- **Goal**: Reduce header clutter on small screens across the app.
- **Scope**:
  - Collapse admin badges + username + theme toggle into a compact mobile nav (drawer or pill stack).
  - Revisit responsive typography tokens so headings/buttons step down earlier on mobile.
  - Ensure primary/secondary buttons maintain clear hierarchy when condensed.
- **Out of scope**: page-specific hero layouts; detail/share widgets.

## Ticket 3 — Feed Spacing & Card Hierarchy Refresh
- **Goal**: Improve scanability of the main requests feed on all viewports.
- **Scope**:
  - Introduce consistent vertical rhythm between cards/sections.
  - Rework meta strip inside cards (status, timestamp) to read left-to-right; align with new detail view pattern.
  - Differentiate primary vs secondary actions (“Send Welcome”, “Share a request”) with color/weight tweaks.
  - Audit gradient background transitions on long scroll to avoid mid-feed flatness.
- **Out of scope**: backend pagination, request detail template.

## Ticket 4 — Background & Motion Finishing Pass (Optional)
- **Goal**: Once layout fixes land, iterate on global gradient/bubble treatment for consistency.
- **Scope**: adjust color stops, opacity, and motion cadence so hero/feed/detail surfaces share a cohesive ambiance without overwhelming content.
- **Trigger**: schedule after Tickets 1–3 merge.
