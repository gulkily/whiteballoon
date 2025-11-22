Problem: When `wb sync push` hits a hub that queued a pending key approval, the CLI surfaces a raw ClickException with the JSON response and stack trace, offering no guidance beyond “Hub upload failed (400).” Operators need a clear one-line summary that references the pending approval ID and hints at resolving it from `/admin` without dumping the stack trace.

User Stories:
- As an operator running `wb sync push`, I want the CLI to tell me the hub queued approval `<id>` for peer `<name>` and to visit `/admin` rather than seeing a scary stack trace.
- As someone reviewing automated push logs (e.g., the `/admin/sync-control` UI), I want the job output to carry the same friendly message so I can triage without reading exception dumps.

Core Requirements:
- Add a dedicated exception class (e.g., `PendingApprovalError`) that carries peer name, pending ID, and optional message so `_push_to_hub` can raise it when the hub responds with `error=peer_key_mismatch`.
- Update the CLI sync push job handler (`_run_push_job` / `_push_to_hub`) to catch this exception and print a user-friendly notice (colorized, no stack trace) that includes: peer name, pending ID, and instructions to approve the key via `/admin`. Exit with a non-zero status so automation knows the push didn’t complete yet.
- Ensure the same handling applies when the sync push command is run directly (outside the admin UI) so the console output remains consistent.

Simple Flow:
1. CLI uploads bundle to hub; hub responds with `400` and `error=peer_key_mismatch`, `pending_id=…`.
2. `_push_to_hub` detects the payload, raises `PendingApprovalError(peer, pending_id)` instead of a generic ClickException.
3. The outer sync job (CLI and admin UI) catches that exception, prints a friendly message, and exits gracefully without a stack trace (still failing the job so it can be retried later).

Success Criteria:
- Running `wb sync push <peer>` against a mismatched hub prints a message like “Hub queued a key approval (pending-id) — visit https://hub/admin to approve” and no traceback.
- The `/admin/sync-control` UI log shows the same friendly text instead of a ClickException dump.
- Other errors (network failure, invalid signature) still raise the normal ClickException with stack trace.
