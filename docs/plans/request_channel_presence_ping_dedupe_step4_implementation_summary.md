## Stage 1 – Shared throttle utilities and storage hooks
- Changes: Added presence storage keys plus local/session storage helpers and scope/payload utilities in `static/js/request-channels.js`.
- Verification: Not run (requires browser session).
- Notes: None.

## Stage 2 – Throttle heartbeat pings without breaking typing
- Changes: Routed periodic heartbeat through `pingPresenceHeartbeat` with per-request throttle and renamed the direct sender to `sendPresencePing`.
- Verification: Not run (requires browser session).
- Notes: None.
