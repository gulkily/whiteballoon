1. CLI listing + UX polish
   - Extend `tools/dev.py` pending-pull helpers to expose a list view; update `wb sync pull` so running without `peer` prints the pending table (peer, key, created, pending ID) and exits.
   - Add `--pending` flag for scripts (list + exit) and refine the friendly message for `--approve` success/failure.

2. Admin UI integration
   - Reuse the existing hub pending store metadata to populate a new “Pending pull approvals” section in `/admin` (similar to push).
   - Add approve/discard POST routes that reuse `_approve_pending_pull` logic (or a shared helper) and render success/error banners.

3. Job log messaging & docs
   - Update `_run_pull_job` to include a link/hint pointing admins to the `/admin` queue when a pending approval occurs.
   - Document the unified queue in `docs/hub/README.md` so operators know they can approve pull keys via UI or CLI.
