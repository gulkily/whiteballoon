# User Permissions Dashboard · Step 2 Feature Description

**Problem**: Admins currently have to open individual profile pages and scan scattered attributes to understand which permissions (admin, peer-auth reviewer, invite scopes, etc.) are in effect and have no way to filter the user list by those permissions or edit them in one unified place.

**User stories**
- As an admin, I want to open the Profiles directory and immediately see each user’s permission summary so I can confirm who has elevated access before approving sensitive actions.
- As an operator, I want to filter the user list by permission flags (e.g., admins, peer-auth reviewers, invite issuers) or other fields like status/email so I can find the right account quickly.
- As the reviewer managing permissions, I want a consistent editor (same layout and controls) for every user so I can toggle roles/attributes without drilling into multiple subpages.
- As an admin concerned about clutter, I want a single control to hide/show the permission details so the directory stays scannable when I only need usernames/contact info.

**Core requirements**
1. Extend the `/admin/profiles` listing to include a permission summary block under each row, rendered via a dedicated CSS class/partial so every user’s permissions share the same layout.
2. Implement a page-wide toggle (e.g., “Show permission panels”) that collapses/expands all permission blocks simultaneously without a full reload; default to collapsed for readability but persist the user’s choice within the session.
3. Within each permission block, surface key flags (admin, peer-auth reviewer, invite quota, other stored UserAttribute permissions) plus inline controls to flip those values (where policy allows) and show immutable metadata (who last changed it, timestamps).
4. Enhance the Profiles filter form to include permission-related filters (checkboxes or select for admin flag, peer-auth reviewer, auto-approve invites) alongside existing username/contact fields; filter results server-side so pagination/counts remain accurate.
5. Keep the detail page (`/admin/profiles/<id>`) authoritative for deeper metadata but ensure any permission edits made from the directory use existing services (`user_attribute_service`, session helpers) and return the list to its previous scroll position.

**Shared component inventory**
- `templates/admin/profiles.html`: Base listing/table layout; will host the new filter controls, permission blocks, and global toggle.
- `templates/admin/profile_detail.html`: Existing per-user detail view; permission block partial should be shared so both views stay consistent.
- `static/skins/base/20-components.css` (and any admin-specific skin files): Needs new styles for the permission-card class, collapsed states, and toggle control.
- `app/routes/ui/admin.py`: Profiles directory handler; must load permission metadata, respond to new filters, and process inline updates.
- `app/services/user_attribute_service.py` + `app/services/peer_auth_service.py`: Provide and mutate permission attributes; ensure helper functions expose the data needed for the directory.

**User flow**
1. Admin visits `/admin/profiles` and sees an updated filter form with permission filters plus a “Show permission panels” toggle (default off).
2. Admin applies a filter (e.g., “Peer-auth reviewers”) and the list refreshes, showing only matching users.
3. Admin toggles “Show permission panels”; permission blocks slide open under each row, displaying badges and controls.
4. Admin expands a permission block, adjusts a setting (e.g., mark user as peer-auth reviewer), and the change saves without navigating away; the block reflects the updated state and metadata.
5. Admin hides the panels again or navigates to a profile detail page, where the same permission partial mirrors the updated information.

**Success criteria**
- Profiles directory displays standardized permission blocks (collapsed by default) for every listed user and they can be shown/hidden globally.
- Filters can limit the list by at least admin flag and peer-auth reviewer status in addition to current fields, and results/pagination remain correct.
- Inline permission edits persist immediately (manual QA via DB inspection) and the UI reflects success/failure without a full page reload.
- Permission block partial is reused on both the directory and profile detail pages to avoid divergent layouts.
- Manual QA walk-through confirms toggling the global visibility control, filtering by permission, and editing at least two permission types all behave as expected.
