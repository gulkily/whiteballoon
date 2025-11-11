# Multi-Instance Sync – Status & Hub Design (2025-11-12)

## Current Progress Snapshot
- **Stage 1 – Data model & privacy flags**: ✅ `sync_scope` fields across users/requests/comments/invites, admin toggles live.
- **Stage 2 – Export/import pipeline**: ✅ `wb sync export/import`, deterministic `.sync.txt` bundles + manifest, import CLI tests.
- **Stage 3 – Peer registry & push/pull**: ✅ `wb sync peers add/list/remove`, filesystem push/pull, admin sync dashboard.
- **Stage 4 – Vouch records**: ✅ Schema + CLI + export/import coverage.
- **Stage 5 – Key management & signing**: ✅ `wb sync keygen`, signed manifests, `bundle.sig`, `public_keys/<key>.pub`, verification on pull/import, README + dashboard UX.
- **Stage 6 – Documentation & bootstrap**: ⚠️ README + dashboard guidance shipped, but execution log / final docs / CI automation still pending.

### Outstanding Items
1. Finish Stage 6 deliverables (execution log updates, Step 4 implementation summary, CI coverage for export/import).
2. Network transport: support HTTPS-based push/pull (hub or direct peer endpoints).
3. Enhanced peer UX (edit/show commands, possible UI management screen).
4. Sync status monitoring (surface last push/pull per peer, hub-side dashboards).
5. Final postmortem once transport + docs are complete.
