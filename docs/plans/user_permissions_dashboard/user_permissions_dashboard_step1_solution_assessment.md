# User Permissions Dashboard · Step 1 Solution Assessment

## Problem statement
Administrators need a reliable way to inspect every permission/role a user currently has, edit those permissions in one place, and browse/filter the full user list by permission flags or other attributes to locate accounts quickly.

## Option A – Enhance existing admin profile pages with collapsible permission cards
- **Pros**
  - Reuses `/admin/profiles` IA so operators stay within a familiar workflow.
  - Minimal routing/auth changes because the page already enforces admin access.
  - Per-user permission blocks (dedicated CSS class + shared partial) keep markup consistent while enabling a page-wide hide/show toggle to reduce clutter.
- **Cons**
  - Profile detail pages are already dense; even with hide/show toggles the page may feel heavy when expanding multiple users.
  - Filtering by permission or status still requires extending the existing listing filters, which can add complexity to legacy query code.
  - Harder to compare users side-by-side; requires jumping between detail pages or expanding multiple cards.

## Option B – Dedicated “Permissions & Roles” workspace
- **Pros**
  - Purpose-built table view can show username, status, key timestamps, and togglable permissions with column filters (permission tags, admin flag, invite source, etc.).
  - Centralizes editing: drawer/modal can load the selected user’s permissions, invite stats, and notes without leaving the table.
  - Enables future expansion (bulk updates, CSV export) without squeezing them into existing profile templates.
- **Cons**
  - Requires new route, template, and authorization plumbing plus data loaders optimized for wide tables.
  - Additional UX/design effort to keep it consistent with other admin skins.
  - Duplicates some profile data unless we invest in shared components right away.

## Option C – CLI-first permission audit tooling
- **Pros**
  - Quick to ship: extend `./wb` commands to list/filter permissions and update attributes from the terminal.
  - Works in headless environments and during incident response when the UI is down.
- **Cons**
  - Fails the stated requirement for an in-app table with filters.
  - CLI-only workflows limit discoverability and are slower for bulk visual audits.
  - Hard to delegate to non-technical admins.

## Recommendation
Pursue **Option A**. Enhancing the existing admin profile UX keeps the effort focused, lets us add a standardized permission-card class per user for consistent rendering, and satisfies the “page-wide toggle to hide/show all permission sections” requirement without introducing a brand-new workspace. We can still expand the profile list filters to include permission attributes, and the shared class + toggle mitigate clutter while giving admins an at-a-glance control surface.
