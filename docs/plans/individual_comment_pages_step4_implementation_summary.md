# Individual Comment Pages – Step 4 Implementation Summary

## Stage 1 – Routing + permission plumbing
- Added `/comments/{comment_id}` to `app/routes/ui/__init__.py` that reuses existing permission checks (pending requests limited to admins/authors) and serializes the comment + parent request data for the template.
- Reused `request_comment_service.serialize_comment` and `_serialize_requests` to keep payloads consistent, including Signal display names when available.
- Stubbed `templates/comments/detail.html` so the new route renders without errors until the full layout ships in Stage 2.
- Verification: Hit `/comments/{id}` for an existing comment plus `/comments/999999` for a missing one to confirm 200 vs. 404 responses.

## Stage 2 – Template + layout reuse
- Built `templates/comments/detail.html` with stacked cards: the canonical `comment_card` plus a request-summary panel that surfaces status, timestamps, description, and a “View full request” action.
- Added responsive styling hooks (`.comment-detail__*`) and a permalink affordance in `templates/partials/comment_card.html`, updating `static/skins/base/30-requests.css` to cover the new layout.
- Verification: Loaded `/comments/{id}` on desktop + mobile; confirmed the comment renders via the shared partial and the request summary links back to `/requests/{id}`.

## Stage 3 – Linking + navigation polish
- Pass `/comments/{id}` permalinks into every request-context comment list (request detail + browse tab + the detail page itself) so the card shows a “Permalink” link alongside other meta actions.
- Swapped legacy `#/comment-id` anchors for the new permalink across moderation/Admin Sync/S comment tables and the combined feed, ensuring every “View comment” action opens the standalone page.
- Verification: Clicked “Permalink” from a request thread, `/browse?type=comments`, the admin insights table, and the Sync dashboard, confirming each route now resolves to `/comments/{id}` with correct permissions.
