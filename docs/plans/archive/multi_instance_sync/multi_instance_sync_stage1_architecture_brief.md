# Stage 1 – Architecture Brief: Multi-Instance Sync

## Problem Snapshot
Operators want to self-host WhiteBalloon nodes, bootstrap with shared data, and selectively sync with other nodes (central hub or peer-to-peer) while retaining private data. Sync can be manually triggered initially. Social graph segments must converge via “vouch” records that retrofit cross-instance trust.

## Data Scope (Initial vs Deferred)
- **Sync now**: users (public profile fields only), requests, request comments, invites (public metadata + tokens marked shareable), invite personalizations that are flagged public, request comments, request status history, vouch records (new), minimal session info for attribution.
- **Local/private only for now**: authentication sessions, half-auth flows, user attributes flagged private (emails, phone), admin audit logs, uploaded invite media unless marked shareable.
- **Out of scope**: binary blobs beyond invite photo URLs, analytics events, future modules.

## Option A – Hub-and-Spoke (Central Relay)
**Idea**: Instances register with a shared hub. They push signed deltas to hub; hub fans out to subscribing peers.
- Pros: simpler peer discovery, single place to reconcile “vouch” records, easier moderation (hub can revoke peers), manual sync command becomes `push` + `pull` from hub.
- Cons: hub is SPOF (though data still lives locally), requires hosting shared infra, privacy enforcement must happen before push (hub can’t know what’s private), high-latency for offline nodes if hub unreachable.
- Considerations: hub stores per-instance outbox, needs auth (mutual TLS or signed tokens). Hub must support schema version negotiation so differing releases can still exchange subsets.

## Option B – Direct Peer Pull/Push
**Idea**: Instances keep a peer list (URL + public key). Manual `sync pull` fetches remote changes; `sync push` hits peers directly.
- Pros: no hub dependency, works even when only two instances exist, easier for tightly trusted clusters.
- Cons: peer discovery/manual config burdensome, each instance must handle queueing/outbox per peer, conflict resolution logic duplicated everywhere. Harder to propagate “vouch” relationships without a registry.
- Considerations: need gossip mechanism for new peer info; operator CLI becomes heavier (manage trust, tokens per peer). Good for small groups but scales poorly without automation.

## Option C – Hybrid (Hub for Discovery + Optional Direct P2P)
**Idea**: Hub acts as directory & optional relay. Instances register, exchange public keys, and can either pull from hub or directly from peers once trust established.
- Pros: Operators can start simple (hub-based) then graduate to direct sync for mission-critical peers. Hub still handles vouch chain + schema negotiation. Allows air-gapped instances to import/export via hub-generated bundles.
- Cons: More moving parts (hub + optional direct flows). Need clear precedence rules (e.g., direct sync overrides hub copy) and more configuration UI. Testing matrix larger.
- Considerations: start with manual commands hitting hub endpoints; later allow CLI to request signed peer contact info for direct sync.

## Privacy & Vouching Concepts
- Every syncable record gains `sync_scope` (private, trusted_peers, public). Private never leaves instance; trusted goes to named peers; public can go to hub.
- New “vouch” record: `vouch{ instance_A, instance_B, signature }` to patch social graph segments. Hub stores vouches and exposes them so invite flows can treat remote users as legitimate.

## Transport & Format
- HTTP(S) JSON endpoints with pagination and signed payloads (HMAC or Ed25519). Manual export/import uses newline-delimited JSON bundles, versioned with schema ID so mismatched instances can skip unknown fields.
- Each payload carries `schema_version`; receivers map fields or ignore extras.

## Recommended Direction
Option C (Hybrid) gives us flexibility: start with manual hub-mediated sync while allowing advanced operators to enable direct peer pull later. Early deliverable can be “Manual sync via hub (push then pull)” with CLI commands and bundle exports. Peer-to-peer direct mode rides on the same signed payload format.

## Open Questions
1. What minimal metadata do we expose for users to keep privacy (e.g., username only vs contact details)?
2. How do we store & rotate signing keys? Are they per-instance secrets or per-peer tokens?
3. Do we need conflict resolution beyond “latest timestamp wins”? For example, request completion toggles from two instances.
4. How will we surface sync status/errors to operators (CLI only, or admin UI dashboard)?
5. Should hubs persist full copies of public data or act only as transient relays?

*Next: Stage 2 – Capability Decomposition.*
