## Stage 1 – Shared throttle utilities and storage hooks
- Changes: Added presence storage keys plus local/session storage helpers and scope/payload utilities in `static/js/request-channels.js`.
- Verification: Not run (requires browser session).
- Notes: None.

## Stage 2 – Throttle heartbeat pings without breaking typing
- Changes: Routed periodic heartbeat through `pingPresenceHeartbeat` with per-request throttle and renamed the direct sender to `sendPresencePing`.
- Verification: Not run (requires browser session).
- Notes: None.

## Stage 3 – Combine thread scopes into shared presence polling
- Changes: Aggregated request IDs across tabs for polling, stored shared presence payloads with TTL checks, and applied updates via the `storage` event.
- Verification: Not run (requires browser session).
- Notes: None.

## Stage 4 – Prune stale tab registrations
- Changes: Added TTL pruning for stored tab scopes and cleared the current tab scope on `pagehide`/`beforeunload` or when no IDs remain.
- Verification: Not run (requires browser session).
- Notes: Scope TTL set to two polling intervals plus a small buffer.
