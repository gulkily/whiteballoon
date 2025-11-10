# Request Comments – Implementation Summary

## Stage 1 – Data model & migrations
- Changes: Added `RequestComment` SQLModel with request/user foreign keys, text body, and timestamps to `app/models.py`, plus unit test ensuring comments persist in an in-memory DB.
- Verification: `pytest tests/models/test_request_comment.py`

## Stage 2 – Comment retrieval & serialization
- Changes: Added `app/services/request_comment_service.py` with helpers to list, create, and soft-delete comments plus validation constants; exposed the service via `app/services/__init__.py`. Added unit tests covering add/list/validation behavior.
- Verification: `pytest tests/services/test_request_comment_service.py`

## Stage 3 – Posting endpoint + validation
- Changes: Added `/requests/{id}/comments` POST handler that enforces full authentication, validates bodies via the service, persists comments, and returns both rendered HTML fragments (for vanilla JS) and JSON metadata. Built comment partial template, context wiring in request detail view, and fetch-based JS to insert comments without reload; added route tests covering success, validation failures, and permission checks.
- Verification: `pytest tests/routes/test_request_comments.py tests/services/test_request_comment_service.py tests/models/test_request_comment.py`

## Stage 4 – UI integration & vanilla JS
- Pending

## Stage 5 – Moderation hooks & documentation
- Pending
