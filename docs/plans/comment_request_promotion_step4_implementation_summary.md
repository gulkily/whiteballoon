# Comment Request Promotion – Step 4 Implementation Summary

## Stage 1 – Promotion service + API skeleton
- **Shipped**: Added `comment_request_promotion_service.promote_comment_to_request` to build new `HelpRequest` rows from existing comments, plus `/api/comments/{id}/promote` so authenticated users (UI or agents) can call the shared logic. Response reuses the canonical `RequestResponse` schema and logs each promotion via the service logger.
- **Verification**: Ran a manual Python script to seed a temporary comment and confirmed the service created/deleted a promoted request successfully (`python - <<'PY' ...`).
