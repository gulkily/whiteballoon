# Half-Auth Shadow Publish – Solution Assessment

- **Problem**: Half-authenticated users should be able to create requests and interact with the app, but their activity must remain invisible until approval. Once approved, the staged activity should automatically become public.
- **Option 1: Server-side staging tables (recommended)**
  - Pros: Clear separation of pending vs. public data; easy to promote on approval; supports moderation tooling; scales to other content types.
  - Cons: Requires new tables/models; promotion logic must be kept in sync; migration effort.
- **Option 2: JSON blob in user session / queue table**
  - Pros: Minimal schema change (single JSON field); simple to “flush” into live tables; keeps drafts attached to session/user.
  - Cons: Harder to query/manage; risk of large blobs; more complex concurrency handling when merging.
- **Option 3: Event log with replay**
  - Pros: Captures all actions as events; easy to replay once approved; extensible to audit/mod tools.
  - Cons: Highest complexity; requires event-processing pipeline; overkill for MVP.
- **Recommendation**: Option 1 – server-side staging tables. Provides a clean separation, straightforward promotion on approval, and is easier to manage/moderate while keeping the implementation understandable.
