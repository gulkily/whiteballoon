Problem: Hub operators have to edit `.sync/hub_config.json` manually when a push fails due to a peer’s mismatched public key, leading to downtime and friction. They want a single confirmation dialog in the hub UI that adds the presented key to the peer’s allowed list and retries the upload automatically.

User Stories:
- As a hub operator, I want a prompt to appear when a peer’s key mismatches so I can review the new key and authorize it in one click.
- As a security-minded admin, I want the prompt to show both the stored key list and the presented key so I can spot malicious changes before confirming.
- As a peer maintainer, I want the hub to retry the bundle automatically after I approve the new key so the push completes without re-uploading.

Core Requirements:
- Detect signature failures caused by public key mismatch, capture the presented key + bundle payload, and log a pending approval per peer.
- Extend peer config to support multiple public keys; the approval flow should append the new key rather than replacing existing ones so rollouts are seamless.
- Add a hub admin UI component (modal or inline dialog) listing pending approvals, highlighting the presented key, existing keys, and offering a single “Approve new key” action.
- On confirmation, append the key to the peer’s list, persist the config, reload settings, and replay the retained bundle upload once.
- Log the action (approver name, timestamps, peer, key fingerprint) for auditing and ensure only authenticated hub admins can approve.

Simple User Flow:
1. Peer uploads a bundle; verification fails because the presented key isn’t in the peer’s allowed list.
2. Hub stores the bundle + presented key in a pending queue and returns a 400 to the peer referencing the mismatch.
3. Hub admin opens the dashboard, sees the pending approval card, reviews the presented key against existing keys, and clicks “Approve new key”.
4. Hub appends the key to the peer entry, reloads settings, replays the saved bundle, and clears the pending queue entry while showing success feedback.

Success Criteria:
- Mismatched keys generate actionable UI prompts without manual config edits.
- Approving the dialog appends the new key, keeps older keys valid, and completes the original bundle ingest without a new upload.
- Audit logs capture each approval (peer, operator, timestamp, key hash), and unauthorized users cannot approve key additions.
