1. Schema bootstrap
   - Dependencies: Step 2 approval
   - Changes: Design SQLite/SQLModel tables for `hub_feed_request` and optional `hub_feed_comment`, add metadata tables for manifest digests + source peers, define Pydantic DTOs for API output.
   - Verification: Run new unit tests (if feasible) or exercise via interactive shell to ensure tables create cleanly; inspect generated schema file.
   - Risks: Overfitting schema before ingest parser defined; migration path must be lightweight since hub bundles already live on disk.

2. Ingest parser service
   - Dependencies: Schema definitions
   - Changes: Build a service that, given a bundle root + peer + manifest digest, walks `requests/*.sync.txt` (and comments if included), parses metadata, normalizes timestamps, and upserts into the new tables with scope filtering.
   - Verification: Manual invocation via CLI or unit test against fixture bundle to confirm deduping (same request ID overwrites), scope filtering, and comment count calculations.
   - Risks: Parsing errors due to unexpected bundle formatting; need to guard against partial ingest.

3. Upload pipeline integration
   - Dependencies: Ingest service
   - Changes: Update hub upload endpoint to initialize the DB (if missing), call ingest after writing bundle files, and record manifest/peer metadata; ensure errors bubble appropriately without breaking existing bundle storage.
   - Verification: Upload a sample bundle and confirm DB rows update, logs show ingest success, and existing API responses stay intact.
   - Risks: Ingest failure blocking uploads; need transactional behavior or clear fallback.

4. Feed API + queries
   - Dependencies: Schema + ingest data available
   - Changes: Implement SQLModel query helpers that paginate/sort requests, add a FastAPI JSON endpoint returning normalized records, and expose comment counts/status tags.
   - Verification: Hit endpoint locally, ensure pagination metadata works, and response matches DB contents; add tests if practical.
   - Risks: Inefficient queries if tables grow; need indexes on updated_at/source identifiers.

5. Reddit-style template & SSR integration
   - Dependencies: Feed API/query helpers
   - Changes: Create a new template (or rework home.html) to render the reddit-style feed using the query results, add pagination/infinite-scroll hooks, and ensure skin helpers can override styling later.
   - Verification: Run hub locally, visit feed, confirm layout matches expectations and data aligns with JSON endpoint.
   - Risks: Template becoming too skin-specific; ensure CSS classes are generic.

6. Progressive enhancement + docs
   - Dependencies: Feed API and template working
   - Changes: Wire optional JS to hydrate/infinite-scroll via the JSON endpoint, document usage for skin developers (README or docs), and note how to switch skins.
   - Verification: Manual test of JS enhancement, confirm docs describe data contract and structured store behavior.
   - Risks: Scope creep if JS becomes complex; keep enhancement minimal and document-only if time constrained.
