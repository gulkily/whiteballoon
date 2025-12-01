# Hub Pull Key Flow — Step 4 Implementation Summary

## Stage 1: Pull metadata capture & exception
- `_pull_from_hub` now verifies signatures without enforcing the expected key up front, caching the downloaded bundle under `data/pending_pull/<peer>/<id>/` when a new key appears.
- Introduced `PendingPullApprovalError` so the CLI surfaces a friendly “pending approval” message (with pending ID) instead of a stack trace when the key mismatches.

## Stage 2: Approval workflow
- Added `wb sync pull --approve <pending-id>` which loads the cached bundle, appends the new key to the local peer registry, re-verifies the tarball, imports it, and cleans up the cache.
- `/admin/sync-control` pull jobs now catch the pending error and log a guidance message so operators know to run the approval command instead of reading a traceback.

## Stage 3: Messaging & docs
- `docs/hub/README.md` now documents the CLI pull approval flow so operators know to run `wb sync pull --approve <pending-id>` after seeing the friendly error message.
