Problem: `wb sync pull` fails with a raw “Signature public key does not match expected peer key” when a remote rotates keys. Operators have to edit the peer config manually and rerun the pull. We want a hub-style approval flow: capture the downloaded bundle, prompt to approve the new key once, append it locally, and replay the import automatically.

User Stories:
- As an operator running `wb sync pull <peer>`, I want the CLI to tell me the new key and ask for confirmation (or instruct me via the UI log) rather than crashing.
- As someone monitoring pulls via `/admin/sync-control`, I want the job log to say “pending key approval” with the presented key so I know to accept it, not a stack trace.

Core Requirements:
- When `_verify_bundle_dir` detects the mismatch, capture the presented key from the signature metadata and save the downloaded bundle to a temporary/persistent cache keyed by peer.
- Introduce a CLI prompt (or structured exception for the UI job) that presents old vs new key and asks for approval. For headless jobs, the exception should carry enough context so `/admin/sync-control` can instruct the operator to run a follow-up command (e.g., `wb sync pull --approve <pending-id>` or similar) without stack traces.
- On approval, append the key to the peer entry in `sync_peers.json`, verify the cached bundle, import the data, and clean up the cache.

Simple Flow:
1. `wb sync pull` downloads bundle, verification fails due to key mismatch.
2. CLI saves bundle + presented key under `data/pending_pull/<peer>/<id>`, raises `PendingPullApprovalError` with instructions.
3. Operator runs `wb sync pull --approve <pending-id>` (or uses a prompt) to append the key and replay the import.
4. After approval, future pulls succeed automatically until the next rotation.

Success Criteria:
- Failed pulls no longer emit stack traces; instead they show a friendly message referencing the pending ID and next steps.
- Approving the pending pull (via CLI or UI job) appends the key locally and imports the saved bundle without redownloading.
- Security posture remains: no auto-trust without explicit approval.
