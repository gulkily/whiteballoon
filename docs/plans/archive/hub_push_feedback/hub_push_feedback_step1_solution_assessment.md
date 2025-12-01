Problem Statement: When a hub push fails due to a pending key approval, the CLI surfaces a raw JSON error (with stack trace), making operators dig through logs instead of receiving actionable guidance.

1. Minimal parsing in the push command — detect `error=peer_key_mismatch` and rewrite the ClickException message to explain that an approval was queued, include the pending ID, and suggest visiting `/admin`.
   - Pros: quick to implement, no architectural changes, keeps existing failure semantics while improving UX.
   - Cons: still throws an exception (so the job/logs show a failure), no retry automation.
2. Structured CLI error object — add a custom exception type or Click result that the sync job can inspect. Instead of dumping a stack trace, the CLI would print a formatted guidance block and exit gracefully, so `wb sync push` in the UI can bubble a clean message and avoid a stack trace.
   - Pros: best operator experience (clear message, no stack trace), allows future callers (CLI or UI) to handle the condition differently.
   - Cons: slightly more work (new exception class, updates to `_run_push_job` and the CLI), but still contained.
3. Auto-approval attempt — have the CLI prompt to approve the key directly (if the user has admin token) and retry automatically.
   - Pros: end-to-end fix with no extra steps for the operator.
   - Cons: complex (requires secure admin token handling, hub API for approval, riskier UX), out of scope for a quick improvement.

Recommendation: Option 2 provides the best balance—introduce a custom `PendingApprovalError` (or similar) that carries the pending ID/peer, have `_push_to_hub` raise it when the hub responds with `peer_key_mismatch`, and update the sync UI/CLI to print a clear friendly message without a stack trace.
