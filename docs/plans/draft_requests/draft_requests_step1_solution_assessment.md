# Draft Requests · Step 1 Solution Assessment

**Problem statement**: Users currently have to compose a full request in one sitting; there’s no way to save in-progress drafts before sharing.

**Option A – Draft status in existing requests table**
- Add a `status = 'draft'` state (or `visibility` flag) to `HelpRequest`, keep drafts in the same table, and only surface them to the author until they publish.
- Pros: Minimal schema changes, reuse existing forms/API, easier to publish by toggling status.
- Cons: Need to ensure drafts never leak to other users (all queries must filter), and historical data/export code must stay aware of the new status.

**Option B – Separate `request_drafts` table**
- Store drafts in their own table tied to the author; copy data into `HelpRequest` when published.
- Pros: Clear separation, no accidental exposure, easier to clean up stale drafts.
- Cons: Requires sync logic at publish time, potential duplication of validation.

**Option C – Client-side autosave only**
- Use localStorage/browser storage to save drafts per device, without server persistence.
- Pros: No backend changes; quick to ship.
- Cons: Drafts don’t move across devices, no server backup, easy to lose.

**Recommendation**: Option A. Adding a draft status to the existing `HelpRequest` keeps publishing simple (status flip) and avoids duplicating models or migrations. We’ll add strict filters to make sure drafts stay author-only until published.
