# Comment Request Promotion – Step 4 Implementation Summary

## Stage 1 – Promotion service + API skeleton
- **Shipped**: Added `comment_request_promotion_service.promote_comment_to_request` to build new `HelpRequest` rows from existing comments, plus `/api/comments/{id}/promote` so authenticated users (UI or agents) can call the shared logic. Response reuses the canonical `RequestResponse` schema and logs each promotion via the service logger.
- **Verification**: Ran a manual Python script to seed a temporary comment and confirmed the service created/deleted a promoted request successfully (`python - <<'PY' ...`).

## Stage 2 – UI affordances + confirmation modal
- **Shipped**: Added a "Promote" action to request comment cards (respecting the same permission check as the API) and rendered a lightweight `<dialog>` modal that pre-fills the comment text, lets the reviewer tweak summary/contact/status, and POSTs to the shared `/api/comments/{id}/promote` endpoint via the new `static/js/comment-promotion.js` helper.
- **Verification**: Loaded a request detail page locally, promoted a seeded comment via the modal, and confirmed the browser redirected to the newly created request.
