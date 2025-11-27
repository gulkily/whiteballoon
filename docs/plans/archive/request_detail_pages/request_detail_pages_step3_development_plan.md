# Request Detail Pages — Step 3 Development Plan

1. **Stage 1: Routing & Serialization Prep**
   - Add `GET /requests/{request_id}` route (UI router) that fetches request + creator username reusing existing service helpers.
   - Ensure route enforces existing visibility rules (readonly flag, half-auth access).
   - Testing: unit tests for serialization helper (if new) and integration test for route access (authenticated vs half-auth).
   - Risks: duplicated logic if helpers aren’t reused; unauthorized access if checks missed.

2. **Stage 2: Detail Template & Layout**
   - Create `templates/requests/detail.html` extending base layout.
   - Present request metadata (status badge, timestamps via `friendly_time`, description, contact email) and add back-link to feed + share affordance.
   - Ensure components align with design system (cards, buttons) and respect dark mode.
   - Testing: manual smoke, template render unit test if feasible.
   - Risks: inconsistent styling with feed, overlooking accessibility (ARIA/labels).

3. **Stage 3: Feed Integration & Navigation**
   - Update feed items (`requests/partials/item.html`) to link titles/badges to detail page; adjust JS if necessary to avoid breaking in-place interactions.
   - Add optional “View details” link for clarity.
   - Testing: manual feed interaction (expand/collapse, mark complete) and ensure links work for readonly contexts.
   - Risks: regressions in existing JS behaviours, link visible to unauthorized viewers.

4. **Stage 4: QA & Documentation**
   - Run pytest + lint (if available) and perform manual checks (dark/light theme, mobile width, half-auth view).
   - Document the new route in README/cheatsheet; note sharing guidance.
   - Update Step 4 implementation summary.
   - Risks: missing documentation updates, overlooked mobile layout issues.
