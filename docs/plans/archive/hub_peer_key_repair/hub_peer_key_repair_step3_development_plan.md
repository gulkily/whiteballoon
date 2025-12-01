1. Peer config schema update
   - Dependencies: Step 2
   - Changes: Extend `HubPeer` to store `public_keys: list[str]`, migrate config loader to support legacy single-key entries, and adjust signature verification to accept any allowed key.
   - Verification: Load sample configs (single vs multi-key) via unit test or manual script to ensure parsing works.
   - Risks: Backwards compatibility; ensure writing config preserves structure.

2. Pending approval store
   - Dependencies: Stage 1
   - Changes: Add lightweight storage (JSON file or sqlite table) to persist mismatched key attempts + bundle payloads keyed by peer until resolved; ensure file permissions are safe.
   - Verification: Trigger a mismatch manually and confirm records are written/read correctly.
   - Risks: Storage bloat if bundles are large; consider size limits or temp dirs.

3. Upload error handling
   - Dependencies: Stage 2
   - Changes: Modify upload endpoint to detect SignatureVerificationError caused by key mismatch, stash presented key + bundle in pending store, and return a structured error.
   - Verification: Simulate mismatch by changing peer key and confirm pending entry is created and error references approval flow.
   - Risks: Distinguishing actual bad signatures from key mismatch; ensure other failures still behave the same.

4. Admin UI & API
   - Dependencies: Stage 2
   - Changes: Create admin endpoints + templates to list pending approvals, show existing keys + new key, and expose a POST action to approve (append key) or discard; include audit logging.
   - Verification: Hit admin UI, approve a pending key, ensure config updates and pending entry clears; check logs.
   - Risks: Ensuring only admins access; managing concurrency if multiple operators act simultaneously.

5. Upload replay workflow
   - Dependencies: Stage 4
   - Changes: After approval, reload hub settings, re-verify the stored bundle using the new key, and push it through the normal ingest path; handle failures gracefully.
   - Verification: Approve a stored bundle and confirm the original push now succeeds without re-upload; check DB ingest.
   - Risks: Bundle corruption during storage; need cleanup if replay fails.

6. Docs & cleanup
   - Dependencies: prior stages
   - Changes: Document the multi-key behavior and approval workflow in `docs/hub/README.md`, update Step 4 summary, and add CLI/admin guidance for removing keys later.
   - Verification: Manual review of docs and ensure Step 4 summary covers completed work.
   - Risks: Missing docs causing confusion; ensure instructions reflect UI labels.
