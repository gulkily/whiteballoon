# Comment Display Cards – Step 2 Feature Description

## Problem
Comments appear in multiple surfaces (request detail list, chat search results, profile history, admin tools) but each template renders author info, timestamps, scope badges, and actions differently, leading to inconsistent UX and higher maintenance.

## User stories
- As an admin, I want comment cards to look and behave the same whether I see them on a request, in search results, or on a profile so I don’t relearn controls.
- As a developer, I want a single shared template/partial I can drop into new comment views so I don’t duplicate markup and CSS.
- As an accessibility reviewer, I want the author/timestamp layout to be consistent, with predictable link targets and ARIA labels everywhere.

## Core requirements
1. Introduce a reusable comment card partial that accepts slots/flags for optional elements (scope badge, action buttons, highlight text).
2. Update key views (request detail list, chat search results fallback, profile comments page) to use the shared component.
3. Ensure the component gracefully handles Signal display names + usernames, linking to profiles + comment anchors as appropriate.
4. Provide minimal CSS utilities so variations (compact vs. full) can share the same base styles.

## User flow
1. Server renders comments using the shared partial; each card shows author display name linking to profile, `@username` tooltip, timestamp linking to anchor, scope badge, and body.
2. In search results, the same partial (or variant) renders match highlights but retains the familiar identity block.

## Success criteria
- Comment cards across pages look the same without regressions in existing behavior.
- New views can include the partial with minimal parameters.
- No extra client-side dependencies introduced.
