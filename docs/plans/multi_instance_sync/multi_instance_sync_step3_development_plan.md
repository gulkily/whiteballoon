## Development Plan – Multi-Instance Sync (Manual v0)

### Stage 1: Data Model & Privacy Flags
- Add `sync_scope` (enum: `private`, `public`) to: requests, request_comments, users (public profile fields), invites, vouches.
- Migrations + admin UI badges (request/comment detail, profile editor, invite form) to toggle scope.
- Tests: model migrations, scope toggle permissions.

### Stage 2: Export/Import Pipeline
- CLI: `wb sync export` writes `.sync.txt` files under `data/public_sync/<entity>/<id>.sync.txt` + manifest.
- Format: RFC822-style headers (`Entity`, `ID`, `Instance`, `Schema-Version`, `Sync-Scope`, `Updated-At`) + JSON body.
- CLI: `wb sync import <dir>` reads files, validates scope/versions, applies updates.
- Manual tests: two local DBs run export/import, verify deterministic diffs.

### Stage 3: Hub Push/Pull & Peer Registry
- CLI: `wb sync push --hub <url>` uploads bundle via HTTP (token auth). `wb sync pull` downloads latest bundle.
- Config: `sync_peers.txt` storing hub/peer info; CLI `wb sync peers add/list/remove` edits it.
- Minimal hub endpoints (FastAPI router) to accept bundle uploads & serve bundles.
- Tests: integration with local FastAPI test client; ensure 403 for unknown tokens.

### Stage 4: Vouch Records
- Schema + service for `vouches` table (`voucher_user_id`, `subject_user_id`, `signature`, `created_at`).
- CLI `wb sync vouch`: prompts operator for username, lists unvouched root users, collects y/n, stores records.
- Include vouches in export/import + manifest.
- Tests: unit tests for CLI helper, ensure duplicates prevented.

### Stage 5: Key Management & Signing
- CLI `wb sync keygen` creates Ed25519 keypair under `.sync/keys/`; export/import commands auto-generate keys if missing (warn operator).
- All bundles include signature file (`bundle.sig`); hub verifies before accepting; pull verifies before import.
- Tests: unit tests for signing/verification, ensure auto-generation happens once and keys persist.

### Stage 6: Documentation & Bootstrap Flow
- Update README/setup to mention `wb sync import data/public_sync` during new instance setup.
- Docs for manual workflow (export → commit → pull) and privacy toggle usage.
- Record each merged change in Stage 4 execution log; prepare Step 4 implementation summary based on log.
