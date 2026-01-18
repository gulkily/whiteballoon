# Full-width Layout · Step 2 Feature Description

**Problem**: Many pages inherit the default `.container` width cap (~960px), leaving unused space on larger screens and causing layout inconsistencies between pages that already opted into full-width sections. We want a unified full-width layout that still keeps readable padding on small devices.

**User stories**
- As an operator on a large monitor, I want the request feed, menu, and admin dashboards to stretch across the viewport so I can see more content without scrolling.
- As a designer, I want one canonical container behavior so we don’t have to manage page-specific hacks to achieve edge-to-edge layouts.
- As a reader on mobile, I still want readable side padding; full-width shouldn’t break existing responsive behavior.

**Core requirements**
1. Update the base template’s `.container` (and related layout wrappers) to use the full viewport width with responsive side padding (e.g., clamp-based `padding-inline`).
2. Ensure special pages (forms, cards) still cap inner content as needed by introducing optional `.container--narrow` utility when necessary.
3. Audit sections that currently nest extra `.container` elements (Menu cards, admin tables) and remove redundant wrappers to avoid double padding.
4. Verify that sticky nav, mobile panels, and modal overlays remain aligned after the container change.
5. Keep the main content area fluid for all templates using `{% block content %}` without per-page overrides.

**Shared component inventory**
- `templates/base.html`: main `.container` wrapper around `{% block content %}` and top nav.
- `static/skins/base/00-foundations.css` / `10-navigation.css`: defines container widths, breakpoints, and spacing.
- Key templates with nested containers (`templates/menu/index.html`, `templates/requests/index.html`, admin views) that may require minor adjustments.

**User flow**
1. User loads any page; both the header and main content span the viewport with consistent side padding that scales by breakpoint.
2. Components that need narrower width (e.g., forms, modals) use the new `.container--narrow` (or rely on card widths) to keep readability.
3. On mobile, nothing changes visually except the removal of unnecessary nested containers.

**Success criteria**
- All standard pages use the full viewport width with consistent side padding (no 960px clamps) confirmed via manual inspection on desktop.
- No regressions on mobile widths; content still maintains at least 16px padding per side.
- Any page that previously relied on the narrow container still looks intentional because it opts into `.container--narrow` or card-based constraints.
