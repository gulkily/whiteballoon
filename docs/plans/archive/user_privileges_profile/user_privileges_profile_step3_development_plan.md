# User Privileges Profile — Step 3 Development Plan

1. **Stage 1: Profile route + auth guard**
   - Dependencies: Existing auth middleware/helpers.
   - Changes: Add `/profile` (or equivalent) route; ensure it requires authenticated session; stub controller/view returning placeholder context.
   - Testing: Manual hit on route as signed-in vs anonymous users; existing auth tests (deferred automated additions).
   - Risks: Route conflicts with existing paths; auth guard misconfiguration allowing unintended access.

2. **Stage 2: Server-side profile data & privilege mapping**
   - Dependencies: Stage 1 route in place; user model with admin/half-auth attributes.
   - Changes: Populate controller/view context with identity fields and privilege descriptors; ensure admin/half-auth flags are available to template.
   - Testing: Manual inspection via Django shell/unit harness (if available) for different user fixtures; note automated tests to follow-up.
   - Risks: Missing data fields or naming mismatches; exposing sensitive attributes inadvertently.

3. **Stage 3: Template + header username link and status indicator**
   - Dependencies: Stage 2 data available to templates; existing header layout.
   - Changes: Build profile template rendering identity and privilege list; update header to render username as link with compact badge showing admin/half-auth state; add minimal styling.
   - Testing: Browser/manual verification across viewport sizes; confirm indicator remains legible and compact; check navigation redirects for anonymous state.
   - Risks: Layout regressions in header; indicator miscommunicating status; accessibility contrast issues.

4. **Stage 4: QA + documentation handoff**
   - Dependencies: Stages 1-3 complete.
   - Changes: Conduct targeted smoke tests (signed-in admin, signed-in non-admin, half-auth user); record intended automated tests; update user-facing docs or release notes as needed.
   - Testing: Manual walkthrough; jot down follow-up automated test plan.
   - Risks: Missing edge cases (e.g., user without email); forgetting documentation updates.
