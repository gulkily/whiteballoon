# Stage 0 – Problem Framing: Multi-Instance Sync

## Problem Statement
Self-hosted operators want to run their own WhiteBalloon instance (clone + run) but also start with shared data, publish select records to other communities, and optionally operate a public hub. Today every instance is isolated: no seeded data, no replication, no way to share only certain records.

## Current Pain Points
- No boundary between private-only data and public/shareable data; everything lives in one DB and stays local.
- New operators start from an empty database; there is no bootstrap dataset or replication flow.
- Collaboration between independent instances (e.g., founders) requires manual exports/scripting.

## Success Criteria (Initial)
- Two independently deployed instances (e.g., founder + co-founder) can trust each other, exchange public data, and remain in sync without manual intervention.
- Operators can flag records as "do not sync" or "restricted" before replication runs.
- A new instance can ingest a starter dataset from another instance or hub within minutes of setup.

## Guardrails
- Minimize new dependencies; prefer simple HTTP/file transports over adding heavy brokers unless absolutely required.
- Keep the implementation incremental and pluggable so single-instance users remain unaffected.
- Maintain the current “clone + run” experience for private deployments; sync must be opt-in.
