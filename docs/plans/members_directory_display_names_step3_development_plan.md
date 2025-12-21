# Members Directory Display Names – Step 3 Development Plan

1. **Stage 1 – Enrich member directory service output**
   - **Goal**: Have `member_directory_service.list_members` return both profile rows and a per-user display-name map so downstream callers no longer issue duplicate attribute queries.
   - **Dependencies**: Existing `user_attribute_service.load_display_names(session, user_ids, group_slug=None)` helper; current pagination/filter clauses inside the service.
   - **Expected changes**: Update `MemberDirectoryPage` dataclass to include a `display_names: dict[int, str]` field and, after fetching profiles, call `load_display_names` with the current page’s user IDs before instantiating the page object. Keep ordering/pagination SQL untouched.
   - **Verification**: Run `/members` and `/admin/profiles` locally to ensure total counts and pagination are unchanged (logging query count via SQL echo, if needed) and confirm the service returns a populated map for users with Signal attributes while omitting others.
   - **Risks / Questions**: Slightly larger payload per page; ensure we guard against `None` IDs to avoid extra lookups. Need to ensure memoized attribute ordering (newest first) stays intact when we reuse the helper.

2. **Stage 2 – Wire `/members` route + template to shared map**
   - **Goal**: Replace the route’s bespoke display-name lookup with the data returned alongside the directory page and render it in the template via the canonical partial.
   - **Dependencies**: Stage 1 must expose the `display_names` map; template already leverages `partials/display_name.html`.
   - **Expected changes**: Remove the direct `load_display_names` call from `app/routes/ui/members.py`, keep only the avatar lookup, and pass `directory_page.display_names` into the template context (as `member_display_names`). Confirm `templates/members/index.html` still sets `profile_display_name = member_display_names.get(...) or profile.display_name` before invoking the partial.
   - **Verification**: Load `/members` with a mix of Signal and non-Signal users to confirm friendly names appear and fall back correctly; toggle pagination/filters to ensure the map updates with each page.
   - **Risks / Questions**: None significant—primary concern is forgetting to handle empty lists, so add guard clauses when deriving avatar/display maps.

3. **Stage 3 – Mirror changes in admin profile directory**
   - **Goal**: Ensure the admin-only directory consumes the same shared map so staff see “Chengyi” instead of raw usernames, keeping parity with the member view.
   - **Dependencies**: Stage 1’s enriched service output; Stage 2’s template pattern for resolving final text.
   - **Expected changes**: Thread `directory_page.display_names` through the `/admin/profiles` route context (e.g., `profile_display_names`) and have `templates/admin/profiles.html` look up each profile’s name before calling `partials/display_name.html`. No additional queries; avatar logic is already separate.
   - **Verification**: Visit `/admin/profiles` as an admin, confirm friendly names render in the table header, and ensure pagination/filter controls still work. Spot-check that permission toggle UI remains unaffected.
   - **Risks / Questions**: Admin list renders more rows per page, so attribute lookup still needs to be batched once; confirm the helper’s query handles up to PAGE_SIZE IDs without performance issues.
