Problem Statement: Operators need visibility into pending pull approvals—`wb sync pull` should list cached pending IDs when run without args, and the `/admin/sync-control` UI should offer an approval action instead of telling humans to drop into the CLI.

1. CLI-only enhancement — extend `wb sync pull` to list pending IDs/files when invoked without `--approve`, but leave the admin UI untouched.
   - Pros: minimal scope, quick to implement, surfaces the necessary meta for terminal users.
   - Cons: admins using the web UI must still shell into the CLI to approve keys; UX mismatch versus push flow.
2. Unified queue + UI action — add a pending pull registry (reusing the cache metadata) and expose it via `/admin/sync-control` (table + buttons) plus a dedicated CLI listing (`wb sync pull --pending`). The UI can trigger the same approval logic via HTTP, keeping workflows consistent.
   - Pros: aligns with push approvals, admins never need CLI access, CLI users still benefit from a discoverable list.
   - Cons: slightly more work (new admin endpoints + template updates), but matches the requirement precisely.
3. Auto-approve in UI only — add UI button that simply shells out to `wb sync pull --approve`. No CLI listing and CLI invocation without peer keeps failing unless user knows pending ID from logs.
   - Pros: easy to hook the UI into existing approval command.
   - Cons: still requires humans to parse logs to copy pending IDs, CLI remains unfriendly.

Recommendation: Option 2—build a shared pending-pull listing and surface it both via `wb sync pull --pending` and the admin console, with approval actions wired into the existing cache + replay logic.
