Problem Statement: When a push fails because a peer's stored public key is stale, hub operators want a single confirmation dialog in the UI that updates the peer entry automatically using the key from the incoming request.

1. Manual UI editor — add an "Edit peer" form in /admin that lets operators paste a new public key and save.
   - Pros: minimal backend changes, reuses existing auth flows.
   - Cons: still manual (copy/paste), multiple clicks, doesn’t leverage the failed push context, doesn’t reduce support load much.
2. On-error inline repair — when the hub detects a key mismatch, stash the presented key and expose a UI prompt showing the diff; with one confirmation the operator updates the peer config and retries the upload automatically.
   - Pros: exactly matches the workflow request (single confirmation), clear audit trail per peer, no extra navigation, smooth for operators.
   - Cons: needs temporary storage for the mismatched key and a secure approval flow, plus logic to replay the upload.
3. Auto-trust toggle — provide a hub-wide flag that automatically accepts new keys on mismatch and rotates them immediately.
   - Pros: zero clicks once enabled; easiest for unattended deployments.
   - Cons: risky (could accept malicious key), no confirmation dialog, diverges from the security expectation.

Recommendation: Option 2 keeps the security posture (explicit confirmation) while minimizing clicks. We can capture the failed key, show a modal in the hub admin UI, and once approved update the config and re-run the upload without manual file edits.
