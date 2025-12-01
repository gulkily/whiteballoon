# Half-Auth Shadow Publish – Solution Assessment

- **Problem**: Half-authenticated users should be able to create requests and interact with the app, but their activity must remain invisible until approval. Once approved, the staged activity should automatically become public.
- **Option 1: Reuse existing tables with `status` flag (recommended)**
  - Pros: No schema change; simple promotion on approval (status flip); consistent with current implementation; minimal risk.
  - Cons: Requires careful filtering to hide pending data; potential for status misuse without guardrails.
- **Option 2: JSON blob in user session / queue table**
  - Pros: Minimal schema change (single JSON field); simple to “flush” into live tables; keeps drafts attached to session/user.
  - Cons: Harder to query/manage; risk of large blobs; more complex concurrency handling when merging.
- **Option 3: Event log with replay**
  - Pros: Captures all actions as events; easy to replay once approved; extensible to audit/mod tools.
  - Cons: Highest complexity; requires event-processing pipeline; overkill for MVP.
- **Recommendation**: Option 1. Reusing the existing `status` flag keeps the implementation lean and aligns with our current progression from `pending` to `open` states.
