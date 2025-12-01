1. Exception plumbing
   - Add `PendingApprovalError` (peer, pending_id, detail) under `tools/` or shared CLI utilities.
   - Update `_push_to_hub` to parse JSON responses; when `error=peer_key_mismatch`, raise the new exception instead of ClickException.
   - Verify behavior with a manual push against a hub that queues approvals.

2. CLI messaging & job handler
   - Catch `PendingApprovalError` inside `_run_push_job`/sync push command, print a friendly message (colored, includes peer/pending id, directs to `/admin`), and exit with non-zero status but no traceback.
   - Ensure standalone `wb sync push <peer>` also adopts the friendly message (wrap call sites as needed).
   - Manual smoke test via CLI and via `/admin/sync-control` job runner to confirm the logs include the new message.
