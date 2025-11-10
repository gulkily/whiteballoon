# Multi-Instance Sync Ideation Checklist

*Adapted from CLI_IMPLEMENTATION_CHECKLIST: each section captures what we need before implementation. Result = detailed design narrative; do not start coding yet.*

## Prereqs
- Confirm baseline deployment story for single instance (docker, bare metal). Document supported runtimes (Python ≥3.10, Postgres, Redis?).
- Define “instance identity” (hostname + public key?). Each instance must have unique ID and advertised base URL.
- Decide minimum viable data set to sync (requests, comments, invites) and what stays local by default.

## Stage 1 – Skeleton & Utilities
- Describe sync transport abstraction (HTTP pull/push, message queue, or pluggable adapters). Outline helper modules for:
  - Instance registry client
  - Payload signer/validator (HMAC or public/private keys)
  - Privacy flags utility (e.g., `sync_scope=public|trusted|private`)
- Specify configuration knobs: `SYNC_MODE` (central, peer-to-peer, hybrid), remote endpoint lists, encryption keys.

## Stage 2 – Environment Bootstrap
- Detail how a fresh instance opts into sync:
  - Command to register with hub (exchanging public keys, selecting datasets).
  - Process for importing initial snapshot from another instance.
  - Fallback when hub unreachable (queue outbound diffs, exponential backoff).
- Plan `.env` additions for sync secrets, hub URL, allowed peers, and privacy defaults.

## Stage 3 – Dependency Check & Background Workers
- List required services: job runner (RQ/Celery), message broker, object store?
- Define health checks: hub reachability, last sync timestamp, queue depth.
- Document admin CLI commands: `wb sync status`, `wb sync run-once`, `wb sync repair`.

## Stage 4 – Commands / Capabilities
(Think of each as a CLI command or API capability we must specify before coding.)

1. `sync init`
   - Inputs: remote instance URL, API token/public key, datasets to follow.
   - Flow: fetch schema compatibility info, download bootstrap snapshot, store trust record.
2. `sync pull`
   - Describe pagination/windowing, conflict resolution order (remote wins vs latest timestamp), and filtering using privacy flags.
3. `sync push`
   - Define change feed (e.g., outbox table). Include batching, retry policy, and how to skip private records.
4. `sync prune`
   - Plan data retention rules for remote-originated records and ability to forget specific peers.
5. `sync privacy`
   - UI/CLI story for marking entities `do_not_sync` or scoping to trusted peers. Must exist before implementation.

## Stage 5 – Testing / Validation
- Enumerate test scenarios: clean bootstrap, recurrent sync, network partition, revoked peer.
- Specify how to run integration tests locally (multiple docker-compose services? in-memory hub?).
- Capture metrics to watch: sync latency, conflict count, number of private records filtered.

## Stage 6 – Documentation & Rollout
- Outline docs to ship before implementation: operator guide, privacy FAQ, troubleshooting tree.
- Define rollout phases: single hub in lab → limited peer mesh → general availability. Include gating criteria for each.

---
**Key Product Requirements Captured**
- *Self-hosted instances*: every user/community can run their own node with optional participation in the mesh.
- *Flexible topology*: support syncing via central hub or direct peer-to-peer (document which transports are available per mode).
- *Selective privacy*: every syncable record must expose `sync_scope` metadata so owners can keep items private or limit them to specific peers.
- *Future design doc*: Use this checklist to produce a comprehensive architecture spec before coding multi-instance sync.
