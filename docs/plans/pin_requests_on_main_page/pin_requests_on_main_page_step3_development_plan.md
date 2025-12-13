# Pin Requests on Main Page — Step 3 Development Plan

## Stage 1 – Pin attribute model + helpers
- **Goal**: Provide a typed helper for reading/writing pin metadata via `request_attributes`.
- **Dependencies**: Existing `request_attributes` table + attribute service utilities.
- **Changes**: Define a dataclass (e.g., `PinnedRequest`) plus helper functions `list_pinned_requests(session, limit)` and `set_request_pin(session, request_id, *, rank, actor_id)` that serialize metadata (rank, actor, timestamps) into attribute values. Implement `clear_request_pin` and ensure writes stay idempotent. Add defensive checks to avoid duplicate rank collisions.
- **Verification**: Unit-level smoke via shell/REPL or temporary CLI (toggle pin, fetch list). Confirm metadata round-trips correctly and that deleted attributes disappear from helper results.
- **Risks**: Attribute JSON drift or malformed payloads—guard with try/except and default fallbacks so a bad attribute doesn’t break the page.

## Stage 2 – Pin/unpin routes + permissions
- **Goal**: Expose server endpoints/actions to pin or unpin a request from UI.
- **Dependencies**: Stage 1 helpers; existing request detail/list routes; shared action menu infrastructure.
- **Changes**: Add POST routes (e.g., `/requests/{id}/pin`, `/requests/{id}/unpin`, `/requests/{id}/pin/rank`) under UI module, checking admin permissions. Operations call helper functions, set flash/status messages, and redirect back (respecting `next` param). Wire CLI-friendly logging.
- **Verification**: Hit endpoints via curl or browser with admin session, confirm success statuses and DB attribute updates; ensure non-admins receive 403.
- **Risks**: Race conditions when multiple admins pin simultaneously—wrap helper writes in transactions and optionally lock ranks.

## Stage 3 – Request feed data plumbing
- **Goal**: Deliver pinned-request data to templates and API responses.
- **Dependencies**: Stage 1 helpers.
- **Changes**: Extend the `/requests` route + JSON API to fetch pinned entries first (limit configurable), annotate each `HelpRequest` with `is_pinned` + `pin_rank`, and inject a `pinned_requests` collection into the template context. Ensure API consumers keep seeing chronological data (pinned block only influences server-rendered HTML for now).
- **Verification**: Load `/requests` and inspect context via debug logging; ensure pinned requests are fetched even when not in the default pagination window.
- **Risks**: Performance hit if helper runs extra queries per request—batch attribute lookups to avoid N+1.

## Stage 4 – UI rendering (pinned block + badges)
- **Goal**: Surface a dedicated "Pinned" section and card indicators.
- **Dependencies**: Stage 3 data.
- **Changes**: Update `templates/requests/index.html` to render a `pinned_requests` block above the main list (reusing `requests/partials/item.html`). Add a small badge/banner via context (e.g., `show_pin_badge=True`) so pinned cards visually stand out. Handle empty state (block hidden when none pinned). Add CSS tweaks for the new block/badge.
- **Verification**: Manual browser check with 0/1/3 pinned entries to ensure layout is responsive and badges show on both pinned cards and elsewhere (detail page if flagged).
- **Risks**: Duplicate cards (pinned + chronological) confusing users—ensure pinned IDs are excluded from the subsequent chronological slice or clearly labeled.

## Stage 5 – Action menu integration + rank management
- **Goal**: Hook pin/unpin controls (and ordering affordances) into the shared menu.
- **Dependencies**: Stage 2 routes and existing action-menu partial.
- **Changes**: When building `request.actions`, append menu entries for pin/unpin (and optional "Move up/down" or "Edit rank" forms). Include hidden fields/HTMX hooks so admins can adjust ranks without leaving the page. Ensure detail view shares the same action set. Update JS (if necessary) so request-feed refreshes reflect new `is_pinned` state.
- **Verification**: Open the menu on a request, trigger pin/unpin/rank operations, refresh the page, and confirm the pinned block updates. Confirm non-admins never see these entries.
- **Risks**: Menu clutter if multiple actions appear—group labels or separators as needed; verify clipboard/copy actions still present for regular users.

## Stage 6 – Reorder UX touchpoint (optional stretch)
- **Goal**: Provide a lightweight interface (modal or admin-only mini form) to edit pin order when >1 request is pinned.
- **Dependencies**: Stage 5 baseline actions.
- **Changes**: Add an admin-only modal or inline form listing pinned entries with numeric inputs; submitting updates ranks via Stage 2 routes. This can reuse the action menu to open the modal.
- **Verification**: Pin 3 requests, adjust their ranks, and confirm the pinned block reorders accordingly.
- **Risks**: Scope creep—consider deferring to a follow-up if ordering UI proves complex.
