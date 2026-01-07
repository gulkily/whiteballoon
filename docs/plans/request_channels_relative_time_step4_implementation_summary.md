## Stage 1 – Shared client-side formatter
- Changes: added `static/js/time-utils.js` with `formatFriendlyTime` mirroring server thresholds; loaded the helper globally from `templates/base.html`.
- Verification: not run (manual browser check needed to confirm helper availability).
- Notes: keep `formatFriendlyTime` in sync with `friendly_time` if server rules change.
