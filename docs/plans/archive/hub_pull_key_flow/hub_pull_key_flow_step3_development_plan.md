1. Metadata capture & exception
   - Update `_pull_from_hub` / `_verify_bundle_dir` to capture signature metadata (presented key) when verification fails due to mismatched key; raise a new `PendingPullApprovalError` that includes peer name, key, and a path to the cached bundle.
   - Add local storage under `data/pending_pull/<peer>/<id>/bundle.tar.gz` similar to the hub’s pending store so we can re-import without re-downloading.

2. Approval workflow
   - Add CLI command/flag (`wb sync pull --approve <pending-id>`) that appends the key to the peer’s config, verifies the cached bundle, and runs `import_sync_data` from the stored tarball.
   - Update `_run_pull_job` in `/admin/sync-control` to catch the new exception and log a friendly message instructing operators to approve the key.

3. Messaging & docs
   - Ensure both CLI and UI logs show clear guidance (peer, pending ID, next steps), similar to the push flow.
   - Document the new pending-pull flow in `docs/hub/README.md` (or CLI docs) so operators know how to approve keys.
