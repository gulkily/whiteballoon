# Request Channel Presence Ping Dedupe — Step 3 Development Plan

1. Stage: Shared throttle utilities and storage hooks
   - Goal: Provide a cross-tab, best-effort throttle, presence payload sharing, and cross-tab ID aggregation for presence updates.
   - Dependencies: Browser `localStorage`, `window` `storage` event, existing `updatePresenceIndicators`.
   - Expected changes: Add helper functions such as `readSharedPresence(key)`, `writeSharedPresence(key, value)`, `shouldSendPresencePing(key, intervalMs)`, `applySharedPresencePayload(payload)`, and `upsertPresenceScope(tabId, requestIds)`; define storage keys for heartbeat, aggregated request IDs, and presence payload timestamps.
   - Verification: Open two tabs and confirm no console errors when localStorage is available; temporarily disable storage (privacy mode) and verify page still operates.
   - Risks or open questions: Storage exceptions or quota errors; ensure helpers fail open to current per-tab behavior.
   - Shared components/API touched: `static/js/request-channels.js` presence helpers.

2. Stage: Throttle heartbeat (POST) pings without breaking typing signals
   - Goal: Ensure only one tab sends the periodic presence heartbeat per interval while typing signals remain responsive.
   - Dependencies: Stage 1 helper functions, existing `pingPresence` and `handleTypingEvent`.
   - Expected changes: Wrap the 8s heartbeat timer to call a new `pingPresenceHeartbeat()` that checks `shouldSendPresencePing('presence-heartbeat', 8000)`; keep typing pings on a separate throttle key or bypass the heartbeat throttle.
   - Verification: With two tabs open, network logs show one POST `/requests/channels/presence` per interval; typing in one tab still triggers a typing ping.
   - Risks or open questions: Over-throttling could suppress typing; confirm heartbeat throttle does not block user-initiated typing updates.
   - Shared components/API touched: `/requests/channels/presence` POST, `static/js/request-channels.js` heartbeat wiring.

3. Stage: Combine thread scopes into a single presence poll and share payload across tabs
   - Goal: Poll presence once per interval for the union of request IDs across all open tabs while keeping indicators current in every tab.
   - Dependencies: Stage 1 helper functions, existing `refreshPresence` and `updatePresenceIndicators`.
   - Expected changes: Each tab writes its current request ID set to storage (scoped by a tab ID + timestamp); the polling tab aggregates IDs across tabs when `shouldSendPresencePing('presence-poll', 9000)` passes, fetches presence for the union, and writes payload plus timestamp to storage; non-polling tabs read the latest stored payload (when fresh) and call `updatePresenceIndicators`; add a `storage` listener to apply new payloads from other tabs.
   - Verification: With two tabs on different threads, only one GET `/requests/channels/presence` per interval; both tabs show presence for their thread lists; closing the polling tab allows another tab to take over.
   - Risks or open questions: Storage payload size limits if many tabs/IDs; stale tab entries need cleanup to avoid inflated ID sets.
   - Shared components/API touched: `/requests/channels/presence` GET, `static/js/request-channels.js` poller.

4. Stage: Prune stale tab registrations and scope data
   - Goal: Ensure aggregated request ID scope reflects only active tabs.
   - Dependencies: Stage 1 storage helpers, Stage 3 scope aggregation.
   - Expected changes: Store per-tab scope entries with `updated_at` timestamps; add TTL-based cleanup (e.g., drop entries older than 2 presence intervals) during aggregation; refresh the current tab’s entry on a timer; optionally clear scope entry on `pagehide`/`beforeunload`.
   - Verification: Open two tabs, close one, and wait for TTL to expire; confirm aggregated scope no longer includes the closed tab’s IDs and polling continues with remaining tab.
   - Risks or open questions: TTL tuning to avoid pruning slow/hidden tabs too aggressively; ensure cleanup does not flap in background tabs.
   - Shared components/API touched: `static/js/request-channels.js` storage scope handling.
