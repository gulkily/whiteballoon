# Pin Requests on Main Page — Step 1 Solution Assessment

**Problem**: Admins cannot highlight urgent or strategic help requests on the main feed, so critical items quickly scroll out of view.

## Option A – Flag on Request model + ordering tweak
- Pros: Minimal schema change (boolean/priority enum), keeps logic inside existing feed query, works across UI surfaces that share ordering.
- Cons: Requires DB migration and app restart; limited to single ordering rule (harder to support per-user pins or multiple pin groups).

## Option B – New `request_pins` table storing pinned request IDs + position
- Pros: No changes to core request schema; supports multiple pins with explicit ordering; simpler to track who pinned what; easy to extend for expiration metadata later.
- Cons: Additional join/query per page load; need admin UI/CLI to manage the table; slightly more DevOps overhead (new table + migrations).

## Option C – Store pins in config/settings (e.g., `.env` or JSON file)
- Pros: Avoids DB migration; quickest path for very small teams; manageable via existing config workflows.
- Cons: Editing config requires deploy access, not just admin UI; no history/metadata; needs app restart to change pins; prone to drift between environments.

## Option D – Reuse existing `request_attributes` key-value table
- Pros: Zero new schema objects—pinned state + ordering live in the flexible attribute table; easy to store extra metadata (who pinned, expiry) inside the attribute value; updates stay transactional with request edits; keeps room for per-tenant or experimental flags without more migrations.
- Cons: Requires robust querying to avoid N+1 reads (need helper that hydrates pins efficiently); relies on convention (must guard against multiple conflicting pin attributes per request); harder to enforce ordering constraints without additional logic.

## Recommendation
Option D. Leveraging the pre-existing `request_attributes` table avoids migrations while still keeping pin state in the database, so admins can adjust pins via future UI/CLI without deploy access. Storing pin metadata (rank, timestamps, actor) in attributes gives us the extensibility benefits we liked from Option B, but with lower operational overhead and faster delivery.
