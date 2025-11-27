## Overview
- Extended the authenticated header to show both the viewer’s role badge and username, adding a profile avatar shortcut that links to a dedicated profile page.
- Introduced a basic profile view so members, admins, and pending users can confirm their account details in one place.

## Implementation notes
- `app/routes/ui.py` now injects `session_username` into template contexts and exposes a new `/profile` route guarded by `require_session_user`, reusing `describe_session_role` for consistent labels.
- Navigation blocks in the request dashboards render the role badge, `@username`, and a styled profile icon; shared styles live in `static/css/app.css`.
- Added `templates/profile/index.html` as the initial profile page with placeholders for future settings.

## Testing
- Automated: Not run (no Python runtime available here).
- Manual: Pending — verify header badge, username, and profile access for admin, member, and half-authenticated accounts after deployment.
