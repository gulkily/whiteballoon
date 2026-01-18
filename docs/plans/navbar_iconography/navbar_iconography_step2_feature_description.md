# Navbar Iconography · Step 2 Feature Description

**Problem**: The primary navbar row is text-only, so it lacks visual anchors and makes it harder to visually differentiate links (especially on large screens or when the Menu page becomes the catch-all for less-used actions). Adding subtle iconography can improve scannability and polish without overwhelming the design.

**User stories**
- As a frequent operator, I want each primary nav link to have a recognizable icon so I can jump to the right destination even when quickly glancing at the bar.
- As an admin reviewing the UI, I want the icons to respect the current theme and brand, avoiding cartoonish emoji or mismatched colors.
- As a mobile user, I want the icons to appear in the mobile slide-out as well, so the nav feels consistent between desktop and phone.

**Core requirements**
1. Introduce inline SVG icons for Requests, Comments, Browse, and Menu links (desktop + mobile nav), and reuse the same icon set on the Menu page cards so the visual language stays consistent.
2. Icons must inherit text color (use `currentColor`) so they adapt to light/dark skins automatically.
3. Add spacing/alignment rules so icons don’t push the nav row out of alignment; ensure accessibility by keeping visible text labels.
4. Provide semantic titles/`aria-hidden` attributes so screen readers still rely on the text label, avoiding duplicate announcements.
5. Optimize SVGs (minified path data, no extraneous metadata) and colocate them in `templates/partials/icons/` for reuse.
6. Update the mobile nav panel markup to include the same icons for parity.

**Shared component inventory**
- `templates/partials/account_nav.html`: primary nav markup; will add inline SVG includes for each link.
- `templates/menu/index.html`: Menu page cards; each card gets the matching icon so the grid reinforces the same symbolism.
- `templates/partials/nav_mobile_panel.html` (if exists) or the nav panel inside `base.html`: ensures icons show in collapsed nav.
- `static/skins/base/10-navigation.css`: spacing between icons/text, consistent sizing.

**User flow**
1. User loads any page; the navbar shows icons + labels for the four primary destinations.
2. Hover/focus states highlight both icon and text together; theme switching updates icon color automatically.
3. Opening the mobile nav panel reproduces the same iconography, and visiting the Menu page shows the same icons beside each card, reinforcing the link mapping across contexts.

**Success criteria**
- All four primary links display an icon without layout jitter; icons adapt to light/dark themes.
- Mobile nav and Menu page show the same iconography, with touch targets remaining at least 44px tall.
- Manual accessibility check confirms icons are ignored by screen readers (text label still read once).
