# Stage 3 – Implementation Playbook: Multi-Instance Sync (v0)

## Capability A – Manual Sync Commands
- **Goal**: Enable two instances to exchange public data via CLI commands only.
- **Tasks**:
  1. Define CLI subcommands: `wb sync export`, `wb sync import`, `wb sync push`, `wb sync pull`, `wb sync status`.
  2. Exporter writes `.sync.txt` files under `data/public_sync/<entity>/<slug>.sync.txt` (deterministic ordering, RFC822-style headers per file).
  3. Importer reads bundle, validates schema version, skips unknown fields, logs conflicts.
  4. Push/pull target hub endpoints: `/sync/export` (POST file), `/sync/import` (GET). Manual authentication via shared token for v0.
  5. Implement per-entity sync scope filter (export only `sync_scope != 'private'`).
  6. Write docs snippet describing manual workflow (push from instance A, pull into instance B).
- **Verification**: Local integration test (two sqlite DBs) plus manual CLI dry run.
- **Risks**: Large exports blocking CLI (address later with streaming). Manual tokens leaked if not rotated.

## Capability B – Privacy Toggle UI
- **Goal**: Allow admins to mark requests/comments/invites/user fields as shareable.
- **Tasks**:
  1. Add `sync_scope` column to each sync-able table (default `private`).
  2. Build reusable UI badge (e.g., “Private / Share”) on request + comment detail pages and invite profile editor.
  3. Hook toggle to backend endpoint (`POST /sync/scope`) enforcing admin auth.
  4. Provide inline hints explaining impact; auto-warn if data contains email/contact info.
- **Verification**: UI smoke test toggling scopes; unit test for permission enforcement.
- **Risks**: Confusing default states; need seeds/migrations.

## Capability C – Public Dataset Store (Git-friendly)
- **Goal**: Stage shareable snapshots that can be committed to GitHub.
- **Tasks**:
  1. Define `.sync.txt` format: header block (Entity, Version, Instance-ID, Updated-At) + body (JSON payload or YAML). Include `Sync-Scope` header.
  2. Export command writes one file per entity instance (user, request, etc.) with stable filenames (`<entity>_<id>.sync.txt`).
  3. Generate manifest file `data/public_sync/manifest.sync.txt` listing all files and checksums.
  4. Document repo workflow: review diffs, commit, include manifest.
- **Verification**: Diff readability check, ensure repeated exports without changes produce no diff.
- **Risks**: Sensitive info sneaking in; rely on privacy toggle + review.

## Capability D – Vouch Records
- **Goal**: Let operators retroactively connect isolated root users.
- **Tasks**:
  1. Add `vouches` table (`id`, `voucher_user_id`, `subject_user_id`, `signature`, `created_at`).
  2. CLI command `wb sync vouch`:
     - Detect current operator username (prompt).
     - List unvouched root users (no inviter + not vouchable yet).
     - Prompt y/n for each, create vouch record (signature placeholder = SHA of record for now).
  3. Export/import includes `vouches/` directory with `.sync.txt` files similar to other entities.
- **Verification**: Unit tests for vouch creation, ensure exported data matches format.
- **Risks**: Duplicate vouches; handle by unique constraint on (voucher, subject).

## Capability E – Peer Registry (Manual)
- **Goal**: Track known peers for future sync commands.
- **Tasks**:
  1. Define `sync_peers.txt` format: repeated blocks with `Peer-ID`, `URL`, `Public-Key`, `Notes`.
  2. CLI commands `wb sync peers list/add/remove` editing the file.
  3. Sync commands read this file to know push/pull targets (hub entry + manual peers).
- **Verification**: CLI tests ensuring file updates are deterministic.
- **Risks**: Manual file edits causing conflicts; instruct operators to use CLI.

## Capability F – Bootstrap Snapshot for New Instances
- **Goal**: Allow new instance to import repo-hosted dataset.
- **Tasks**:
  1. Document `./wb sync import data/public_sync` as part of setup instructions.
  2. Provide check ensuring schema compatibility before import.
  3. Add optional `wb sync init --from repo` command that runs import + registers peers from repo defaults.
- **Verification**: Fresh DB test using exported bundle; confirm data appears and privacy flags remain intact.
- **Risks**: Mixed schema versions; rely on schema headers + warnings.

*Next: Stage 4 Execution Log (pending your review + commit).* 
