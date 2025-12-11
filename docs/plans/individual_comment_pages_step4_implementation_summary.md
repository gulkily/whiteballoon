# Individual Comment Pages – Step 4 Implementation Summary

## Stage 1 – Routing + permission plumbing
- Added `/comments/{comment_id}` to `app/routes/ui/__init__.py` that reuses existing permission checks (pending requests limited to admins/authors) and serializes the comment + parent request data for the template.
- Reused `request_comment_service.serialize_comment` and `_serialize_requests` to keep payloads consistent, including Signal display names when available.
- Stubbed `templates/comments/detail.html` so the new route renders without errors until the full layout ships in Stage 2.
- Verification: Hit `/comments/{id}` for an existing comment plus `/comments/999999` for a missing one to confirm 200 vs. 404 responses.
