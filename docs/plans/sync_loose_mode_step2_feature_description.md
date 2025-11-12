## Problem
Strict hub mode requires every peer to be pre-configured with name/token/public-key. For ad-hoc collaborations and local testing, operators want a “loose” mode where peers can auto-register themselves during push/pull without human intervention.

## User Stories
- As a hub owner, I can enable auto-registration for uploads so new peers can push bundles without editing config files first.
- As a hub owner, I can separately allow auto-registration for downloads so peers can pull after proving ownership of a signed bundle.
- As an operator of a new peer, I can push/pull once using my token/public key, and the hub records me automatically for future runs.

## Core Requirements
- Hub config accepts two flags: `allow_auto_register_push` and `allow_auto_register_pull`, both defaulting to `false` to preserve current behavior.
- When `allow_auto_register_push` is true, `POST /api/v1/sync/<peer>/bundle` auto-creates a peer entry if unknown, using the provided token/public key. Same for pull when `allow_auto_register_pull` is true.
- CLI sends the peer’s public key with push/pull requests so the hub can register it (e.g., header `X-WB-Public-Key`).
- Auto-registered peers are persisted to the hub config (or adjunct store) so subsequent strict-mode restarts still recognize them.
- Responses indicate whether the peer was auto-registered for auditing.

## User Flow
1. Hub admin toggles one or both loose-mode flags in config.
2. New peer runs `./wb sync push hub-loose` with token + public key; hub creates entry and accepts bundle.
3. Peer (if allowed) runs `./wb sync pull hub-loose`; hub auto-registers for pulls if needed, verifies signature, and serves bundle.
4. Hub persists the new peer info; later the admin can tighten controls or edit tokens via config/UI.

## Success Criteria
- With flags disabled, behavior matches today (404 for unknown peers).
- With push auto-register enabled, first-time uploads succeed and create a peer record containing hashed token + public key.
- With pull auto-register enabled, first-time downloads succeed (provided bundle signature matches the supplied key) and the peer record persists.
- CLI automatically includes the public key so no manual step is required for the peer operator.
