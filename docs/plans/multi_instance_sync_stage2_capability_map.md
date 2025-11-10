# Stage 2 – Capability Map: Multi-Instance Sync

## Release Scope (v0)
1. **Manual Hub Sync (Two Nodes)**  
   - Capabilities: `sync export`, `sync import`, `sync push`, `sync pull` (manual CLI).  
   - Data set: requests, request comments, users (public profile fields), invites + optional personalization, vouch records, any record flagged "public".  
   - Defaults: everything private; admins opt-in per record.

2. **Privacy Tagging UI**  
   - Add "Share / Keep Private" toggle to every sync-able entity (requests, comments, invites, and individual user datapoints such as bio/contact)—small, consistent badge inline.  
   - Backed by `sync_scope` (private default) stored per record/datapoint.  
   - Surfaces warning if admin toggles public on data with private fields (e.g., request contact email).

3. **Public Dataset Store**  
   - Define git-friendly format (`*.sync.txt` bundles with headers, e.g., RFC822-style).  
   - CLI command `wb sync export --public` writes files under `data/public_sync/`.  
   - Repo maintainers can review/commit these files to seed new instances.

4. **Vouch Record Foundation**  
   - Schema + service for `vouch` entries (who trusts whom, signature placeholder).  
   - Export/import along with other public data to stitch social graph segments retroactively.

5. **Peer Registry (Manual)**  
   - Config file or CLI command to list known peers (URL, description).  
   - For v0, no automated discovery—operators edit `sync_peers.txt` (text block per peer) or run `wb sync peers add ...` to seed CLI commands.

## Deferred / Backlog
- Automated failure handling + status dashboards.
- Direct peer-to-peer sync automation.
- Schema migration negotiation beyond "skip unknown fields".
- Fine-grained scopes (trusted peers vs public vs private).

## Dependencies & Notes
- Export format must be append-only, deterministic ordering for Git diffs.  
- Manual import must detect schema version mismatches (warn + skip).  
- Privacy UI relies on existing admin permissions; no change to roles.  
- CLI commands reuse existing `wb` launcher.

*Next: Stage 3 – Implementation Playbook (after review/commit).*
