# Request Comments – Implementation Summary

## Stage 1 – Data model & migrations
- Changes: Added `RequestComment` SQLModel with request/user foreign keys, text body, and timestamps to `app/models.py`, plus unit test ensuring comments persist in an in-memory DB.
- Verification: `pytest tests/models/test_request_comment.py`

## Stage 2 – Comment retrieval & serialization
- Changes: Added `app/services/request_comment_service.py` with helpers to list, create, and soft-delete comments plus validation constants; exposed the service via `app/services/__init__.py`. Added unit tests covering add/list/validation behavior.
- Verification: `pytest tests/services/test_request_comment_service.py`

## Stage 3 – Posting endpoint + validation
- Changes: Added `/requests/{id}/comments` POST handler that enforces full authentication, validates bodies via the service, commits to the DB, and returns rendered comment fragments plus JSON metadata for the frontend. Added route tests covering success, validation failures, and auth checks.
- Verification: `pytest tests/routes/test_request_comments.py tests/services/test_request_comment_service.py tests/models/test_request_comment.py`

## Stage 4 – UI integration & vanilla JS
- Changes: Request detail template now renders the discussion section (list, form, alerts) plus comment partial and new CSS. Added `static/js/request-comments.js` to handle fetch-based posting and DOM insertion with graceful fallback.
- Verification: Manual browser test; covered indirectly by route tests (HTML snippet path).

## Stage 5 – Moderation hooks & documentation
- Changes: Added admin-only delete endpoint/forms for comments (supports JSON + fallback), updated JS to remove comments inline, tweaked partial/template for controls, and documented the feature in README.
- Verification: Manual smoke test of delete button (admin) and README update.
