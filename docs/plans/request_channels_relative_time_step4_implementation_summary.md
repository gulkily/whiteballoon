## Stage 1 – Shared client-side formatter
- Changes: added `static/js/time-utils.js` with `formatFriendlyTime` mirroring server thresholds; loaded the helper globally from `templates/base.html`.
- Verification: not run (manual browser check needed to confirm helper availability).
- Notes: keep `formatFriendlyTime` in sync with `friendly_time` if server rules change.

## Stage 2 – Request channels timestamp formatting
- Changes: switched `static/js/request-channels.js` to call the shared `formatFriendlyTime` helper with a locale fallback for invalid/missing labels.
- Verification: not run (manual check needed in `/requests/channels` to confirm no hour-only labels beyond 24h).
- Notes: consider periodic refresh if auto-updating timestamps becomes required.
