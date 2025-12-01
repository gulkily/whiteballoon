## Problem
Independent WhiteBalloon operators need a way to bootstrap from shared data and selectively sync public records (requests, comments, invites, user bios) with other instances or a hub while keeping private records local. Today every instance is siloed and either starts empty or requires manual exports.

## User Stories
- As an operator, I can export public records from my instance into git-friendly bundles so others can bootstrap from them.
- As an operator, I can pull public bundles (or hub data) into a fresh instance to avoid starting from scratch.
- As an admin, I can mark any sync-able record (request, comment, invite, profile datapoint) as private or shareable directly in the UI.
- As an operator, I can use CLI commands to manually push/pull data between my instance and my co-founder’s instance or a central hub.
- As an operator, I can retroactively “vouch” for root users so disconnected social graphs merge across instances.

## Core Requirements
- Manual CLI commands: `wb sync export/import/push/pull/status` operating on `.sync.txt` bundles sorted by entity.
- Git-friendly export format: RFC822-style headers + body (`*.sync.txt`), deterministic ordering, manifest file with checksums.
- Privacy toggles embedded in request/comment/invite detail pages and profile editor; `sync_scope` defaults to private.
- Hub endpoints (or shared repo) to host exported bundles; peer registry stored in `sync_peers.txt` for future direct connections.
- Vouch record schema + CLI to patch social graph segments; included in export/import flow.
- Manual keypair generation (`wb sync keygen`) producing per-instance signing keys for payload authenticity.

## User Flow
1. Operator runs `wb sync keygen` on both instances to create signing keys.
2. Admin reviews records, toggling privacy badges to mark which items are public.
3. Operator runs `wb sync export` to generate `.sync.txt` files and manifest under `data/public_sync/`; optionally commits to repo.
4. Operator runs `wb sync push` to upload bundle to hub (or shares repo). Peers run `wb sync pull`/`import` to ingest data.
5. If social graph segments remain disconnected, operator runs `wb sync vouch` to retro-invite root users; vouches sync like other entities.
6. Execution log records each merged change; future automation can build on the same artifacts.

## Success Criteria
- Two instances (e.g., founders) can exchange data entirely via CLI commands without touching DB internals.
- Privacy defaults prevent accidental sharing; only records explicitly toggled “Share” appear in exports.
- Fresh instance can import repo-hosted bundles and see non-private requests/comments immediately.
- Vouch records allow remote users to appear trusted for invites.
- The export format is stable/deterministic so Git diffs stay readable.
