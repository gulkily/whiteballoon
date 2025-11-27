## Problem
Request pages have no discussion channel, so members can’t ask clarifying questions or share progress inline with the request itself.

## Options
- **Server-rendered comments + vanilla JS insertion**
  - Pros: Keeps core rendering in FastAPI/Jinja (no new frameworks) while a lightweight JS snippet posts comments via `fetch` and injects the new markup without a full reload; minimal code surface, progressive enhancement friendly.
  - Cons: Requires writing both the HTML partials and the JS updater, handling optimistic UI/error states manually, and ensuring the endpoint can serve both HTML and JSON responses.
- **Pure server-rendered thread (full reload)**
  - Pros: Simplest backend, no JS beyond existing assets, easier caching.
  - Cons: Every comment submit reloads the page, which feels sluggish and loses scroll position for long threads.
- **Realtime/async channel (WebSocket or third-party)**
  - Pros: Live discussion and notifications, future-ready for richer collaboration.
  - Cons: Major infra/design jump (WebSockets, background workers, permissions) and not necessary for initial commenting.

## Recommendation
Implement the hybrid approach: render comments server-side, expose a `POST /requests/{id}/comments` endpoint that returns the rendered comment snippet, and use a small vanilla JS module to append it in place (with graceful fallback to full reload). This satisfies the no-HTMX constraint while delivering an immediate, modern-feeling experience.
