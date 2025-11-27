## Problem
Members need a 2-degree social map (inviter chain above them and invitees below them) and we want to cache each user’s map in a dedicated table so repeated visits don’t re-run graph traversals.

## Options
- **Server-rendered tree + per-user cache table**
  - Pros: Reuses invite graph service + templates, rendering stays synchronous, cache table stores serialized 2-degree trees for quick reads, minimal JS.
  - Cons: Need cache invalidation when invites change, stored payload size grows with large invitee sets, still limited interactivity.
- **JSON graph API + cached payload**
  - Pros: API serves the cached map for reuse in multiple clients (web, admin tooling), enables richer client-side interactions.
  - Cons: Requires new endpoint, auth handling, and frontend rendering code; doubles caching work (API + UI) for little short-term benefit.
- **Background job to precompute broader social graphs**
  - Pros: Can power analytics + notifications, supports future >2-degree needs.
  - Cons: Introduces job orchestration + storage overhead today, overkill when UI only needs 2 degrees.

## Recommendation
Build the server-rendered view backed by a per-user cache table. We can limit traversal to 2 degrees in both directions, serialize/store the resulting structure, and reuse it on repeat visits with lightweight invalidation when a relevant invite relationship changes. This keeps scope tight while honoring the caching requirement and leaves the door open to expose the cached data via an API later if needed.
