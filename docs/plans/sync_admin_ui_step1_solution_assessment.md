## Problem Statement
Admins need to review peer configuration, update hub credentials, and trigger push/pull operations without leaving the browser; today those tasks require terminal access to the server.

## Options
- **A. Extend existing `/sync/public` dashboard with lightweight forms + server-side jobs**
  - Pros: Reuses current templates/styles, minimal learning curve, can call existing CLI helpers via background tasks; fastest path to ship.
  - Cons: Page may become crowded, synchronous requests could block if push/pull takes long.
- **B. Build a dedicated Sync Control Center (new route + HTMX/JS interactions)**
  - Pros: Purpose-built UI for peers/logs, easier to add progress indicators and historical records; can isolate operations in async endpoints.
  - Cons: More design/dev effort; risks duplicating data already shown elsewhere.
- **C. Expose REST API + encourage external dashboard (Grafana/etc.)**
  - Pros: Highly flexible, enables automation beyond our UI; clean separation of concerns.
  - Cons: Higher security surface, still leaves admins without a first-party UI, requires extra tooling to be useful.

## Recommendation
Pursue **Option B**: add a dedicated Sync Control Center within the admin interface. It keeps UX cohesive, gives room for richer peer controls (forms, progress modals), and still leverages our existing backend/CLI primitives. We can start simple (list peers, edit tokens, buttons to trigger push/pull) and layer on status/history later without overwhelming the legacy `/sync/public` page.
