# Request Channels Relative Time — Development Plan

1) Shared client-side formatter
- Goal: Provide a reusable JS formatter that mirrors the server-side `friendly_time` thresholds.
- Dependencies: Reference `app/routes/ui/helpers.py` for canonical rules; no API or DB changes.
- Expected changes: Add `static/js/time-utils.js` with a global helper (planned signature: `formatFriendlyTime(value, now = new Date()) -> string`); include it in `templates/base.html` before other scripts that may consume it.
- Verification approach: Manual spot-check in console with a few ISO timestamps (recent, 2 hours, 3 days, older than a month, future).
- Risks/open questions: Browser `Date` parsing inconsistencies for non-ISO strings; ensure load order doesn’t break consumers.
- Canonical components/API touched: `app/routes/ui/helpers.py` (reference behavior), `templates/base.html` (shared script include).

2) Replace request-channels relative time logic
- Goal: Use the shared formatter for the sidebar timestamps so long hour counts roll up to days/weeks and dates.
- Dependencies: Stage 1 helper available globally; existing `data-timestamp` attributes remain intact.
- Expected changes: Update `static/js/request-channels.js` `updateRelativeTime` to call `formatFriendlyTime` and remove the hour-only logic; keep a safe fallback for invalid dates.
- Verification approach: Open `/requests/channels` with older items; confirm no timestamps show >24h in hours and formatting matches `friendly_time` thresholds.
- Risks/open questions: Auto-updating timestamps over time remains a deferred enhancement (tracked in `todo.txt`).
- Canonical components/API touched: `static/js/request-channels.js` (channel list rendering).
