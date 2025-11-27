## Problem
Operators need to run their own WhiteBalloon instances, seed them with public data, and selectively sync shareable records (requests, comments, invites, user bios) with other instances or a public hub while keeping private data local.

## Options
- **Central hub relay**
  - Pros: Simple peer discovery, single place to reconcile “vouch” graph patches, predictable manual workflow (`push`/`pull`).
  - Cons: Hub becomes SPOF, must host extra infra, privacy enforced only client-side.
- **Direct peer-to-peer sync**
  - Pros: Works for tiny trusted clusters with no hub dependency.
  - Cons: Manual peer management, duplicated conflict resolution, harder to stitch social graph.
- **Hybrid (hub directory + optional direct sync)**
  - Pros: Start with manual hub-mediated CLI sync, later enable direct pulls; hub still stores vouch info and bootstrap bundles; supports manual import/export via git-friendly files.
  - Cons: Slightly more configuration (hub + peers), needs rules for precedence when both hub and direct copies exist.

## Recommendation
Pursue the hybrid approach: build manual CLI commands that export `.sync.txt` bundles, allow pushing/pulling through a lightweight hub, and store peer metadata in `sync_peers.txt`. Include per-record privacy toggles (private by default) plus vouch records so disconnected graphs can merge. Direct peer sync can reuse the same payload/signing format as a future enhancement.
