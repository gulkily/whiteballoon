# Recurring Request Archiving — Step 1 Solution Assessment

**Problem statement**: Admins need a way to archive all requests produced by a recurring template in one action instead of closing each run manually.

**Option A – Template-level archive sweep (bulk update by attribute)**
- Pros: Leverages existing `RequestAttribute` link between requests and templates, so we can target the full set without schema changes; straightforward UI affordance (“Archive all runs” button) on the recurring templates page; job can reuse existing request status transitions to keep analytics intact.
- Cons: Blocking HTTP request might time out if a template has hundreds of runs unless we add a background task; cannot preview which requests will be touched without additional UI work; relies on attribute integrity (missing tags would be skipped).

**Option B – Introduce recurring batches + archive queue**
- Pros: Creates an explicit `recurring_batches` model that groups runs up front, enabling richer management (preview, staged actions, history); batch queue could drive other lifecycle actions (e.g., re-open last month’s chores) and expose progress feedback for long operations.
- Cons: Requires new database schema + migrations; adds parallel grouping concept in addition to existing template/run tables; significantly longer implementation time for the first use case; still needs logic to walk historical runs to populate batches retroactively.

**Recommendation**: Proceed with Option A. It keeps scope limited to UI + service additions on the existing recurring template surface, avoids migrations, and hits the admin use case (one-click archive) fastest. We can mitigate long-running operations by iterating through runs in manageable chunks or offloading to an async task later if needed.
