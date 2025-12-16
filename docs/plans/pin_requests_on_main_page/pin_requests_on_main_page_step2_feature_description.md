# Pin Requests on Main Page — Step 2 Feature Description

## Problem
Critical or time-sensitive help requests disappear from the Requests landing page once newer items arrive, forcing admins to chase links manually instead of steering attention to the most urgent needs.

## User Stories
- As an admin, I can pin a request so it visibly leads the main Requests page until I unpin it.
- As an admin, I can manage the order of multiple pinned requests to highlight the most urgent ones first.
- As an admin, I can remove a pin without deleting or editing the underlying request content.
- As a community member, I immediately see which requests are pinned when I open `/requests`, before the chronological feed.

## Core Requirements
- Store pin metadata (rank/order, actor, timestamps) using the existing `request_attributes` key-value table so no schema change is needed.
- Surface a "Pinned requests" block at the top of `templates/requests/index.html`, limited to a small number (e.g., three) and visually distinct from the chronological list.
- Reuse the canonical request card partial (`templates/requests/partials/item.html`) for both pinned and normal entries; pinned cards gain a badge/label.
- Surface the pin/unpin controls inside the shared action menu component on request cards (list + detail views) so no extra inline buttons are added.
- Ensure fallback behavior when no pins exist (pinned block hidden, chronological feed unchanged) and when pinned requests are completed/removed.

## Shared Component Inventory
- `templates/requests/partials/item.html` (Request card): reused for pinned entries with a small badge/state indicator so we do not fork markup.
- `templates/requests/partials/list.html` (Chronological grid container): stays as-is; new pinned block will live alongside but not replace this component.
- `templates/requests/index.html` (Requests landing layout + hero card): will host the pinned block near the hero and continue embedding the list partial; no structural rewrite required.
- `templates/requests/detail.html` (Individual request view) and admin-only action bar: may gain the pin/unpin affordance but continues to reuse the shared request metadata layout.
- `request_attributes` storage + corresponding service layer (to be implemented if missing): acts as the backing store so API/routes simply read/write attributes instead of adding new models.

## User Flow
1. Admin opens the Requests page (or a request detail page) and clicks a new "Pin to main page" action on a request card.
2. The system records/updates a `request_attributes` entry (e.g., `pin.rank=1`) and confirms the action inline.
3. The Requests landing page queries pinned attributes first, renders the "Pinned requests" block (sorted by rank), and then shows the regular chronological feed beneath.
4. Admin optionally drags/reorders pins or edits rank numbers; the attribute values update, and the pinned block reflects the new order on refresh (live or after reload).
5. When an admin unpins a request, the attribute entry is deleted; the UI hides the badge and removes the card from the pinned block.

## Success Criteria
- Admins can pin/unpin and reorder requests without database migrations or server restarts.
- `/requests` consistently renders a pinned block (when pins exist) above the standard feed, limited to the configured maximum and clearly labeled.
- Pinned cards reuse the canonical layout while displaying an additional badge/label signaling their status.
- Removing the last pin collapses the pinned block automatically, leaving the rest of the page unchanged.
- Telemetry/logs (or at least admin feedback) confirm the actions execute without errors for consecutive pin/unpin cycles.
