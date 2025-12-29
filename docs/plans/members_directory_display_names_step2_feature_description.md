# Members Directory Display Names – Step 2 Feature Description

## Problem
Members browsing `/members` still see raw usernames for most people, even though Signal-sourced display names already appear elsewhere (chat logs, request feeds). That inconsistency makes it hard to recognize familiar people quickly and erodes trust in the roster.

## User Stories
- As an authenticated member, I want the directory to show recognizable names so I can scan for specific people without deciphering long usernames.
- As someone who invited friends, I want the list to reflect the names we used in Signal so I can confirm they joined successfully.
- As an administrator, I want the admin profiles table to mirror the member-facing names so I can cross-reference identities across surfaces.

## Core Requirements
- `/members` must render the best-known display name (Signal-derived when available, falling back to username) for every listed profile.
- Admin profiles directory must consume the same data so staff see identical names when auditing accounts.
- The solution must reuse the existing `signal_display_name:*` attribute data; no schema changes or backfills.
- Pagination, filtering, and visibility rules in `member_directory_service` cannot regress; the display-name enrichment must piggyback on the existing query results.
- Templates must still fall back to `@username` via `partials/display_name.html` when no attribute exists.

## Shared Component Inventory
- `user_attribute_service.load_display_names(...)` already powers chat/comment display names; we will extend/reuse it for directory pages rather than duplicating lookup logic.
- `partials/display_name.html` remains the canonical renderer—directory templates should continue to call it with the resolved `display_name`/`username` pair.
- `member_directory_service.list_members(...)` becomes the shared backend source of profile lists + display-name map so both `/members` and `/admin/profiles` can reuse identical data without repeated attribute queries.

## Simple User Flow
1. Member visits `/members` (or admin visits `/admin/profiles`).
2. Server queries visible users through `member_directory_service.list_members` with filters/pagination.
3. Service collects the matching user IDs and loads any `signal_display_name:*` attributes, preferring newest values.
4. Template receives the `member_display_names` map (plus existing avatars) and renders each entry through `partials/display_name.html`.
5. Viewer can filter/paginate as before; display names stay in sync across all pages.

## Success Criteria
- Every profile shown on `/members` or `/admin/profiles` displays a Signal-derived name when that attribute exists, otherwise falls back gracefully.
- No additional queries are triggered per row; attribute lookups happen once per page render inside the service layer.
- QA run with mixed users (with/without Signal metadata) shows identical names between `/members`, `/admin/profiles`, and chat comment authors.
- Filters, pagination counts, and access controls produce the same results before and after the change.
