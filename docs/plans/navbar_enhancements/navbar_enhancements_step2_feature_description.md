# Navbar Enhancements · Step 2 Feature Description

**Problem**: The primary navigation mixes high- and low-frequency actions, duplicates admin labeling, and places critical links (Menu, Sign Out) inconsistently, making it harder for power users to reach their usual destinations quickly and leaving the overall bar visually uneven.

**User stories**
- As a frequent operator, I want the main navbar to list my common destinations first (Requests, Comments, Browse/People, Menu) so I can jump there without opening the Menu page every time.
- As an admin, I only want to see the “Admin” badge once so the bar feels uncluttered while still reminding me I have elevated access.
- As a casual member, I want the navbar to feel consistent—primary links styled the same way, utility actions grouped—so it’s easy to learn where everything lives.

**Core requirements**
1. Split the nav into primary links (left) and a utility rail (right) housing avatar, role badge, notification/menu triggers, etc.
2. List top destinations (Requests, Comments, Browse/People, Menu) in the primary row using consistent button styling and spacing.
3. Remove “Sign Out” from the top bar; make sure it exists inside the Menu page (and optionally the avatar dropdown) so it remains reachable.
4. Collapse the redundant admin labeling: show a single “Admin” chip in the utility rail when the viewer is an admin; remove the second badge near the username.
5. Keep the dedicated Menu page for low-frequency actions and ensure the navbar still links to it.
6. Ensure responsive behavior: on narrow screens, the primary links should wrap/stack gracefully while the utility rail reflows below or behind a toggle.
7. Audit and standardize typography/colors so the bar feels cohesive (align chip sizes, button text casing, etc.).

**Shared component inventory**
- `templates/partials/account_nav.html`: current navbar markup and admin badges; will be reorganized into primary + utility sections.
- `static/skins/base/10-navigation.css` (or equivalent): navbar styles; needs updates for the split layout, chip alignment, responsive behavior.
- `templates/menu/index.html`: “Menu” landing page; will gain Sign Out link (if absent) and may need minor styling adjustments.
- `app/routes/ui/__init__.py` (context provider) and any layout partials that expose menu entries or session metadata; ensure they still deliver the data needed for the reorganized navbar.

**User flow**
1. User signs in and sees the updated navbar with Requests/Comments/Browse/Menu on the left, avatar + single Admin chip on the right.
2. Clicking “Menu” still loads the dedicated Menu page, which now includes Sign Out (and any infrequent actions).
3. Admins see the “Admin” chip only once; regular users don’t see a role chip but retain the avatar + username.
4. On mobile, the primary links collapse into a stacked list or horizontal scroll while the utility section remains accessible (e.g., below the links or via a compact dropdown).

**Success criteria**
- At least 4 high-frequency destinations are accessible directly from the primary nav without opening Menu.
- Sign Out appears only on the Menu page (and/or avatar dropdown) and disappears from the top bar.
- Admin role indicator renders exactly once and remains visible at typical viewport widths.
- Header retains visual consistency: uniform typography, spacing, and alignment across links/chips, validated via manual QA on desktop + mobile breakpoints.
