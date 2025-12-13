# Step 1 – Solution Assessment: Comment LLM Tag Store

**Problem**: Persist the batched LLM analyses (summaries/tags) in an idempotent SQLite database that the frontend can query, without disrupting existing runs.

**Option A – Extend main app database**
- **Pros**: Frontend already has ORM models; no extra connection logic; easier to enforce relationships to requests/comments.
- **Cons**: Requires new migrations, riskier deploy; heavier coupling between experimental LLM data and transactional tables; harder to prune/rebuild runs.

**Option B – Dedicated SQLite file (adjacent to current artifacts)**
- **Pros**: Mirrors current JSONL location (`data/comment_llm_insights.db`); easy to rebuild by replaying stored runs; isolates failure/IO from primary DB; simple to ship with CLI-only changes now.
- **Cons**: Frontend needs a secondary connection (or API endpoints to proxy); data eventually must be synced or exposed through app services.

**Option C – Import into analytic store only (DuckDB/Parquet)**
- **Pros**: High-performance analytics; easy to run ad-hoc queries.
- **Cons**: Requires new tooling stack; doesn’t help near-term frontend exposure.

**Recommendation**: Option B. Add a `data/comment_llm_insights.db` SQLite database with tables for runs and per-comment analyses. The CLI writes idempotently after each batch (same as current JSONL), and backend services can read from that DB (or ingest later) without migrating the main schema yet. Keeps deployment simple while giving us structured querying immediately.
