# Request Comments – Implementation Summary

## Stage 1 – Data model & migrations
- Changes: Added `RequestComment` SQLModel with request/user foreign keys, text body, and timestamps to `app/models.py`, plus unit test ensuring comments persist in an in-memory DB.
- Verification: `pytest tests/models/test_request_comment.py`

## Stage 2 – Comment retrieval & serialization
- Changes: Added `app/services/request_comment_service.py` with helpers to list, create, and soft-delete comments plus validation constants; exposed the service via `app/services/__init__.py`. Added unit tests covering add/list/validation behavior.
- Verification: `pytest tests/services/test_request_comment_service.py`

## Stage 3 – Posting endpoint + validation
- Pending

## Stage 4 – UI integration & vanilla JS
- Pending

## Stage 5 – Moderation hooks & documentation
- Pending
