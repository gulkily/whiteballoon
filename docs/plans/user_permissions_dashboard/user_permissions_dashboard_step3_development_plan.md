# User Permissions Dashboard · Step 3 Development Plan

## Stage 1 – Directory filter plumbing + permission metadata loader
- **Dependencies**: Step 2 spec, existing `member_directory_service` + `/admin/profiles` route
- **Changes**:
  - Extend `MemberDirectoryFilters` with permission-focused fields (e.g., `role_filter` enum for admin/all/non-admin and `peer_auth_reviewer` tri-state) plus helper normalization.
  - Update `_apply_filters` to respect new fields (simple `User.is_admin` checks plus a subquery or `exists` clause against `UserAttribute` for the `peer_auth_reviewer` flag) while keeping pagination counts accurate.
  - Parse the new query parameters inside `admin_profile_directory`, surface them in the context (flags for whether filters are active), and make sure pagination links preserve every filter/toggle input.
  - Introduce a lightweight helper (e.g., `user_permission_service.load_many`) that collects per-user permission metadata (admin flag, peer-auth reviewer attribute, timestamps/actor IDs from `UserAttribute`) for a batch of user IDs so templates can render consistent cards without extra queries.
- **Verification**: Manually hit `/admin/profiles` with combinations like `?role=admin`, `?peer=1`, and both at once; confirm row counts/pagination update and the template receives permission metadata for every user on the page (can log/inspect context temporarily).
- **Risks**:
  - Filtering by `peer_auth_reviewer` requires joining attributes, which could regress performance if not scoped to the target key; mitigate with targeted subqueries.
  - Pagination URLs may drop new query params if helper functions aren’t updated; double-check generated links.

## Stage 2 – Permission card partial, filters UI, and global toggle
- **Dependencies**: Stage 1 metadata + filter plumbing
- **Changes**:
  - Update `templates/admin/profiles.html` filter form to add the new permission selectors (radio/select inputs for role + peer-auth reviewer) and expose helper text so admins know how to combine filters.
  - Create a reusable partial (e.g., `templates/admin/partials/permission_card.html`) that receives a `User` plus its permission summary and renders the standardized block with badges, status rows, and metadata, wrapped in a dedicated class for styling.
  - Add a page-level toggle control (button or switch) that shows/hides every permission card. Use a small progressive-enhancement script (inline or bundled) to persist the preference in `localStorage` and toggle `data-permissions-visible` on the container; also render the server-side default state so the page is usable without JS.
  - Extend `static/skins/base/20-components.css` (or a scoped admin skin) with styles for the permission card, collapsed states, and the toggle control.
- **Verification**: Load `/admin/profiles`, expand the new filters (ensure they submit), toggle the “Show permissions” control, refresh to verify the persisted preference, and inspect the DOM to confirm every row includes the standardized card structure (even when hidden).
- **Risks**:
  - Toggle UX could drift between JS-enabled and disabled environments; ensure the default collapsed server render still hides cards without requiring JS.
  - Adding more content per row increases page height; watch for layout regressions on small screens.

## Stage 3 – Inline permission editing flows
- **Dependencies**: Stage 2 partial + metadata loader
- **Changes**:
  - Inside the permission card partial, add forms/buttons to toggle key permissions (e.g., admin flag, peer-auth reviewer attribute) and expose read-only rows for immutable metadata (invite counts, last updated).
  - Add a new admin-only POST endpoint (e.g., `/admin/profiles/{id}/permissions`) that accepts an action (`grant_admin`, `revoke_admin`, `peer_auth_enable`, etc.), validates guardrails (prevent demoting the last admin or stripping your own admin without confirmation), updates the `User` or `UserAttribute`, commits, and redirects back with flash messaging.
  - Ensure the inline actions reuse existing services (`peer_auth_service`, `user_attribute_service`) rather than duplicating business logic, and emit log lines for auditing.
  - Wire the template buttons to the new endpoint (include CSRF token if/when available) and show success/error alerts near the table or card.
- **Verification**: Promote/demote a test account’s admin flag and peer-auth reviewer status from the directory; reload to verify the card updates immediately and check the database values manually (e.g., via `sqlite3` or CLI).
- **Risks**:
  - Accidental self-demotion or removal of the last admin; add explicit checks and error messaging.
  - Concurrent edits could stale the permission summary; ensure the redirect reloads fresh data and consider optimistic UI only after the POST succeeds.

## Stage 4 – Detail page reuse + final QA
- **Dependencies**: Stages 1–3 complete
- **Changes**:
  - Replace the bespoke permission snippets on `templates/admin/profile_detail.html` with the shared permission card partial so directory and detail views stay in sync.
  - Pass the same permission summary data into the detail route context (reuse the loader with a single user) and ensure inline actions behave identically (detail page should also submit to the new permission endpoint for parity).
  - Add final polish: ensure flash messages from inline edits surface near the toggle/filter controls, document the new filters/toggle in admin help text, and spot-check responsive behavior.
- **Verification**: Walk through `/admin/profiles/{id}` for multiple users: confirm the card renders, toggle permissions here too, and verify the directory view reflects changes. Run a full flow: filter for peer-auth reviewers, expand cards, toggle permissions, collapse cards again.
- **Risks**:
  - Forgetting to include the permission summary in the detail context would break the partial; guard with asserts/logging.
  - Shared partial must account for contexts where some data (e.g., invitation stats) might be missing; ensure default values don’t crash the template.
