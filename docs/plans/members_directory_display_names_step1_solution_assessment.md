# Members Directory Display Names – Step 1 Solution Assessment

**Problem**: The `/members` directory still shows raw usernames (e.g., `signal-harvard-st-commons-chengyi`) even though other surfaces like `/requests/channels` render friendlier Signal-derived display names, leading to inconsistent identity cues.

## Option A – Join display-name attributes in the directory query
- **Pros**
  - Reuses existing `signal_display_name:<slug>` attributes without schema changes.
  - Keeps canonical data in one place; updates immediately reflect everywhere.
  - Minimal user-facing risk; only affects presentation.
- **Cons**
  - Requires an additional lookup layered onto the paginated members query; careless joins could hurt performance.
  - We still need to pick the “right” slug when a user belongs to multiple Signal groups, so fallback logic may remain fuzzy.

## Option B – Denormalize into a `users.display_name` column
- **Pros**
  - Every surface can read a single column, eliminating per-page attribute lookups.
  - Simplifies future features (CLI output, invite trees) that need the same field.
- **Cons**
  - Requires a schema migration plus backfill job.
  - Needs a write-path policy (which group wins when names differ?) and moderation safeguards.
  - Larger blast radius if we mis-populate the column.

## Option C – Allow members to set their own preferred name in settings
- **Pros**
  - Gives users agency to override auto-imported handles.
  - Works even for people who never joined a Signal cohort.
- **Cons**
  - Adds new UI/API work and moderation considerations.
  - Doesn’t solve the immediate need to reuse Signal values, so we’d still need Option A/B as a fallback.

## Recommendation
Pursue **Option A**. We already capture Signal display names in user attributes; loading them alongside avatars in the members directory is the smallest, least risky path to consistent names. We can refine slug selection heuristics (e.g., prefer the newest attribute per user) without schema changes, and if we later need a true canonical `display_name` column we can revisit Option B with more evidence.
