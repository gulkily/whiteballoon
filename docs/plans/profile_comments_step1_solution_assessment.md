# Profile Comments – Step 1 Solution Assessment

**Problem statement**: Members can view profile pages (including imported Signal chat personas) but cannot read any of that person’s past comments, making it hard to evaluate credibility or follow context.

## Option A – Inline server-rendered comment stream
- Pros:
  - Reuses existing request/comment services, so no new APIs are required.
  - Works for both native WhiteBalloon accounts and mapped Signal profiles by funneling through the same server-render path.
  - Keeps everything accessible without JavaScript, matching current progressive-enhancement approach.
- Cons:
  - Initial page load grows heavier if a user has many comments.
  - Requires careful pagination + permission checks inside the profile route.

## Option B – Lazy-loaded comment panel via dedicated endpoint
- Pros:
  - Keeps the base profile lightweight; comments load only when expanded or scrolled into view.
  - Endpoint can return both standard request comments and Signal-only annotations without refactoring existing profile routes.
  - Easier to add filters (e.g., request-only vs. Signal-only) because the API response can be tailored per request.
- Cons:
  - Adds new client-side JS and increases complexity versus today’s minimal profile template.
  - Harder to ensure accessibility/offline parity if the JS layer fails.

## Option C – Separate “activity” subpage linked from profiles
- Pros:
  - Allows richer historical views (paging, search, filters) without bloating the main profile.
  - Can share the same layout for human accounts and Signal chat avatars, giving parity across data sources.
  - Easier to gate behind auth roles if activity should be limited to admins.
- Cons:
  - Adds extra navigation steps; users must click away from the profile to see basic context.
  - More templates + routes to maintain, and a risk that people miss the new page entirely.

## Recommendation
Adopt **Option B**. A lazy-loaded panel balances performance with discoverability: the main profile remains quick, but comments (from both native and Signal sources) surface inline once requested. The API/endpoint also gives us a clean seam to layer filters and future activity types without rewriting the profile route every time.
