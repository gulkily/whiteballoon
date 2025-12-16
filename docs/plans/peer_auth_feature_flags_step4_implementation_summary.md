# Peer Auth Feature Flags · Step 4 Implementation Summary

## Stage 1 – Settings + env plumbing
- Added `feature_peer_auth_queue` / `feature_self_auth` booleans to `Settings`, backed by `WB_FEATURE_PEER_AUTH_QUEUE` and `WB_FEATURE_SELF_AUTH` env vars, defaulting to false.
- Documented both flags in `.env.example` so operators can toggle them without code edits.
- Verification: Python REPL (`from app.config import get_settings`) confirmed the values reflect env overrides.

## Stage 2 – Peer queue gating
- Wrapped all `/peer-auth` routes (GET + approve/deny) in a feature flag guard; when disabled, calls 404 and the template shows a “disabled” banner.
- Updated `menu`/admin panels so peer-auth links only render when the peer flag is true, preventing dead links.
- Verification: Toggled `WB_FEATURE_PEER_AUTH_QUEUE` locally, confirmed the queue disappears and `/peer-auth` returns 404; re-enabled and observed normal behavior.

## Stage 3 – Self-auth gating
- Added `feature_self_auth` context to login pending views and wrapped `/login/verify` so it returns a disabled message when the flag is off.
- Updated `auth/login_pending.html` to hide the self-verify form (showing guidance to contact a peer) unless the flag is enabled.
- Verification: Toggled `WB_FEATURE_SELF_AUTH` locally; confirmed the form disappears + POST returns 403 when off, and that self-auth completes successfully when on.

(Stage 4 pending.)
