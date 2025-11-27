# User Attributes Schema — Step 1 Solution Assessment

**Problem statement**
- We need a flexible schema to capture user metadata (e.g., inviter) without requiring new columns for each future attribute.

**Option A – JSON attributes column on `users`**
- Pros: Single migration; supports arbitrarily nested metadata; easy to extend via code without schema churn; SQLModel/Pydantic handle JSON fields well.
- Cons: Harder to index/query specific keys; must enforce validation in application logic.

**Option B – Separate `user_attributes` key/value table (preferred)**
- Pros: Normalized structure; allows indexing per attribute key; straightforward to enforce data types per attribute; easy to audit changes by tracking rows.
- Cons: Requires joins/lookups for reads; slightly more complex upsert logic; still needs conventions for structured values.

**Option C – Event log of attribute changes**
- Pros: Auditable history; no schema churn for new attributes; rich analytics.
- Cons: Slower to query “current value”; requires aggregation layer; overkill for simple metadata like inviter.

**Recommendation**
- Choose Option B: introduce a `user_attributes` table storing `user_id`, `key`, `value`, and timestamps. This keeps the schema normalized, indexable, and ready for future extensibility while capturing inviter relationships cleanly.
