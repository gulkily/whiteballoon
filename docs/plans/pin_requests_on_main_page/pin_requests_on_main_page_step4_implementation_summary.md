# Pin Requests on Main Page — Step 4 Implementation Summary

## Stage 1 – Pin attribute helpers
- Added `RequestAttribute` SQLModel and a dedicated `request_pin_service` that stores pin metadata (rank, actor, timestamps) as JSON in the attribute table.
- Helper functions cover listing pins, enforcing the configured limit, setting/clearing pins, and swapping ranks.
- Manual REPL checks confirmed attribute rows create/update/delete correctly and gracefully skip malformed payloads.

## Stage 2 – Pin routes & permissions
- Introduced admin-only POST routes (`/requests/{id}/pin`, `/unpin`, `/pin/reorder`) that wrap the helper functions and redirect back to the originating page.
- Routes respect the configured limit and block non-admins via the existing `require_admin` dependency.
- Verified via browser (admin session) that pin/unpin/reorder endpoints mutate attributes and limit enforcement errors return 400.

## Stage 3 – Feed plumbing
- Request serialization now includes `is_pinned`/`pin_rank` fields so both templates and the `/api/requests` endpoint know which entries are pinned.
- The `/requests` view fetches pinned entries separately (ignoring filters), removes them from the chronological list, and injects a `pinned_requests` collection into the template context.
- Confirmed pinned requests still render even if they’ve scrolled beyond the default feed window.

## Stage 4 – UI rendering
- Inserted a "Pinned requests" card above the main feed (only when no filters are active) that reuses the canonical `requests/partials/item.html` partial and adds a visual "Pinned" chip.
- Added corresponding skin styles for the pinned block and badge, ensuring dropdowns aren’t clipped by the card container.
- Smoke-tested across default, paper, and terminal skins to ensure layout + badges render correctly with ≤3 pins.

## Stage 5 – Action menu integration & ordering
- The shared action menu now exposes pin/unpin/move-up/move-down entries (only for admins). Forms carry a `next` parameter so routes can redirect back without JS.
- `static/js/request-feed.js` mirrors the server markup: pinned badges appear in dynamically-rendered cards, menus include pin actions, and pinned entries are filtered out of the chronological refresh list to avoid duplicates.
- Verified pin actions from both the main feed and detail page, including reordering via the "Move up/down" options, and confirmed the pinned block updates after page reloads.

## Stage 6 – Docs & limits
- Documented the `WB_PINNED_REQUESTS_LIMIT` env var in `DEV_CHEATSHEET.md` and honored it across helpers/routes (`default=3`).
- No additional UX for bulk reordering shipped in this pass; admins can bump pins via the menu controls.

## Overall Verification
- Ran manual flows: pin/unpin/reorder requests, complete pinned requests, test copy-link + completion actions, and ensure pinned badges persist.
- Skins rebuilt via `./wb skins build`; no automated tests were added per guidelines.
