Problem Statement: When `wb sync pull` downloads a bundle signed by a new key, the CLI hard-fails with “Signature public key does not match expected peer key,” forcing operators to manually edit `sync_peers.json` and rerun. Users want the same low-friction flow as push (approve once via hub admin, no local config edits).

1. Auto-append on hub download — mirror the push-side change: when the hub serves bundles it would trust any stored key, but that doesn’t help the CLI which still has the old expected key. Not viable without changing the CLI trust model.
2. CLI pending approval flow — teach `_pull_from_hub` to detect the mismatch, stash the downloaded bundle locally, and prompt the operator to approve adding the new key (similar to push but client-side). Once approved, append the key to the local peer, import the bundle automatically, and avoid manual edits.
   - Pros: smooth UX (single confirmation), local control (no hub change), keeps trust boundary because the operator explicitly approves the new key.
   - Cons: requires new local storage for pending bundles and peer updates.
3. Automatic trust rotation — automatically append any new key encountered during pull and proceed.
   - Pros: zero friction.
   - Cons: security risk (rogue hub could send any key), undermines explicit approval requirement.

Recommendation: Option 2 — implement a CLI-side pending approval flow similar to the hub push UX: cache the bundle + presented key, prompt the operator (or log a friendly message in the sync UI), append the key locally once approved, then replay the import.
