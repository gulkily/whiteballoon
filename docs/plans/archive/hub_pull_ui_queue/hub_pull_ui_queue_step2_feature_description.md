Problem: Pending pull approvals are hard to discover—`wb sync pull` fails unless you already know the pending ID, and the `/admin/sync-control` UI doesn’t list or approve pending pull keys. We need a unified queue that exposes pending entries both in the CLI and the admin UI, with single-click approval mirroring the push flow.

User Stories:
- As a CLI operator, if I run `wb sync pull` without a peer I want to see a table of pending pull entries (peer, key, created timestamp, pending ID) so I can approve and retry without digging into files.
- As an admin in `/admin/sync-control`, I want to see pending pull approvals with “Approve” buttons right in the UI (just like push) so I don’t have to drop into the CLI when resolving pull-related mismatches.
- As a job reviewer, I want pull logs to embed a link or reference to the pending queue instead of a stack trace, keeping UX consistent across push and pull.

Core Requirements:
- Extend the CLI to support `wb sync pull --pending` (or running without peer) to list pending entries, and wire `--approve` to the existing cache replay logic with friendlier messaging.
- Expose pending pull data via the admin UI (new section or combined queue), showing pending ID, peer, presented key, created timestamp, and actions (approve/discard/delete cache).
- Add backend endpoints or reuse existing ones to handle approval/discard requests from the UI, invoking the same logic as the CLI (append key locally, replay cached bundle, remove entry).
- Update `/admin/sync-control` job logs to link back to the pending queue when a pull hits `PendingPullApprovalError`.

Simple Flow:
1. Pull job queues a pending approval (as today). CLI exits with friendly message; UI job logs a pending status referencing the queue.
2. Operator visits `/admin`, sees both push and pull pending queues, clicks “Approve” under pull entry.
3. Server replays the cached bundle via the existing helper, appends the key locally, and clears the entry; UI shows success.
4. CLI users can alternatively run `wb sync pull --approve <pending-id>`; listing is available via `--pending` or running without arguments.

Success Criteria:
- `wb sync pull` without peer shows pending entries when they exist, and `--approve` logs a concise success message.
- `/admin/sync-control` surfaces pending pull approvals; approving from the UI completes the import without CLI steps.
- Pull job logs and CLI output no longer require stack traces; they point operators to the unified queue.
