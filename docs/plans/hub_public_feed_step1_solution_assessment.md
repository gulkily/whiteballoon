Problem Statement: Hub operators need a reddit-style public feed sourced from the synced bundles so visitors can browse the latest public requests and future skins can restyle it without reworking data plumbing.

1. On-demand directory reader — render the feed by scanning `data/public_sync` and parsing each `.sync.txt` file on every HTTP request, then piping the records into a new Jinja template.
   - Pros: zero new storage, fastest to ship, reuses existing hub FastAPI + template stack.
   - Cons: repeated filesystem work for every page load, no normalized data layer for other skins/APIs, harder to paginate or filter as the number of records grows.
2. Cached snapshot service — introduce a lightweight parser that materializes the bundle contents into an in-memory/JSON snapshot keyed by manifest digest, expose that data via a hub service + JSON endpoint, and let the reddit-style template consume the cached snapshot.
   - Pros: amortizes parsing cost per bundle, creates a reusable data contract for future skins or API consumers, enables pagination/sorting without re-reading files, and keeps infra simple (no DB).
   - Cons: requires snapshot invalidation logic and a background refresh hook after uploads, slightly more work than direct reads.
3. Structured ingest store — import bundle data into a small SQLite/SQLModel database on upload and drive the feed from real tables with query support.
   - Pros: powerful querying/filtering, easiest to power multiple skins, analytics, or search later; durable historical data; natural place to add indexes, pagination, and moderation flags.
   - Cons: highest complexity for the hub (new migrations, integrity checks, pruning), risk of divergence from bundle source, adds write-heavy code to a previously stateless service.

Recommendation: Option 3 (structured ingest store) best matches the long-term goal of a reddit-style hub that can evolve into multiple skins—storing parsed bundles in SQLite lets us normalize requests/comments once, add pagination/filtering without re-reading the filesystem, and gives future themes or APIs a stable query surface even if the hub restarts.
