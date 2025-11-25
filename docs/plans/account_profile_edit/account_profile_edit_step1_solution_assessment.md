## Problem
Members cannot edit their contact details or profile photo after signup, so they must ask admins for every tweak, slowing self-service updates.

## Options
- **Server-rendered settings form (current stack only)**
  - Pros: Reuses existing FastAPI/Jinja patterns, no new frontend tooling, straightforward validation, integrates with current auth/session guards.
  - Cons: Requires careful CSRF/session handling, synchronous image uploads may block request thread, UI refresh might feel basic compared to modern account pages.
- **HTMX/AJAX-enhanced form with live previews**
  - Pros: Inline field validation, smoother profile-photo preview without full reload, incremental saves reduce failure impact.
  - Cons: Introduces more complex frontend state + JS, higher test surface, still relies on same backend endpoints underneath.
- **Dedicated API + SPA widget (React/Vue)**
  - Pros: Richest UX, easy drag/drop uploads, future-proof for mobile app reuse.
  - Cons: Heavy lift versus today’s stack (new build tooling, bundle hosting, auth tokens), longer timeline and more maintenance.

## Recommendation
Implement a standard server-rendered settings form first. It aligns with the existing stack, keeps backend/photo upload work contained, and we can later sprinkle in HTMX enhancements once the endpoints and validation are solid.
