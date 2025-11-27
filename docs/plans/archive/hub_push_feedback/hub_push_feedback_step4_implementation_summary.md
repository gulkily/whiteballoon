# Hub Push Feedback — Step 4 Implementation Summary

## Stage 1: Exception plumbing
- Introduced `PendingApprovalError` (subclass of `click.ClickException`) carrying peer + pending ID context.
- `_push_to_hub` now inspects hub error payloads; when `error=peer_key_mismatch` it raises the structured exception so callers can act without parsing JSON.

## Stage 2: CLI messaging & job handler
- Click automatically prints the friendly guidance when `wb sync push` hits the pending state, eliminating stack traces.
- `_run_push_job` in `app/routes/ui/sync.py` now detects `PendingApprovalError`, logs a concise "pending approval" message, and records the job as a non-fatal pending state so `/admin/sync-control` shows actionable guidance instead of a traceback.
