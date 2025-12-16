# Members list page — Step 3: Development Plan

## Stage 1 — Member directory query/service foundation
- **Goal**: Reuse admin query logic but add member visibility filtering (public scope or inviter relationship) via a shared helper.
- **Dependencies**: Existing `admin_profile_directory` query, `user_attribute_service` with invite metadata.
- **Changes**: Extract a `member_directory_service` in `app/services/` that wraps the existing `select(User)` logic, adds filters, and exposes a `list_members(viewer, page, filters)` returning records + pagination metadata. Update `user_attribute_service` to add helper for fetching invite relationships in bulk if needed. No DB schema changes.
- **Verification**: Manual REPL or unit test stub calling the service to ensure filtering behaves for admin vs member vs private invite scenarios.
- **Risks**: Performance regression if invite lookups require per-row queries; mitigate by fetching relevant attributes in one query.

## Stage 2 — `/members` route + template wiring
- **Goal**: Provide a member-facing route/controller that renders the card-based directory using the new service.
- **Dependencies**: Stage 1 service ready.
- **Changes**: Add `@router.get("/members")` in `app/routes/ui/members.py` or extend existing UI router, gated by `require_session_user` (full auth). Pass dataset + filters to a new `templates/members/index.html`. Add nav link in `partials/account_nav.html`. Ensure context includes viewer role to adjust card links. No API/DB changes.
- **Verification**: Manual smoke by logging in as admin/member, hitting `/members`, checking filtering/pagination.
- **Risks**: Accidentally exposing private profiles if service usage is incorrect.

## Stage 3 — Card layout + CSS utilities
- **Goal**: Build the responsive card grid and ensure badges/links match spec.
- **Dependencies**: Stage 2 template.
- **Changes**: Implement card markup with avatar placeholder, username, joined date, contact chip (conditional), scope badge, and profile link CTA. Add lightweight CSS rules (e.g., `.members-grid`, card spacing) in existing stylesheet. Ensure pagination + filters styled consistent with member tone. No new JS.
- **Verification**: Manual browser check at different breakpoints (desktop/mobile) plus screen-reader order sanity.
- **Risks**: Layout regressions if CSS collides with existing classes.

## Stage 4 — QA + documentation
- **Goal**: Verify requirements, document behavior, and prep for launch.
- **Dependencies**: Previous stages complete.
- **Changes**: Update README or admin docs to mention `/members`. Write Step 4 implementation summary per process. Perform manual QA checklist covering admin/member visibility, filters, pagination, and navigation link. No code changes beyond docs.
- **Verification**: Manual walkthrough recorded in Step 4 summary.
- **Risks**: Missing edge cases (e.g., no public users) without explicit QA.
