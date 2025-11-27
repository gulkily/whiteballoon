## Stage 1 – Data model & migrations
- Dependencies: Existing `help_requests`, `users` tables.
- Changes: Add `RequestComment` SQLModel (id, help_request_id, user_id, body, created_at, deleted_at). Update schema integrity tooling/migrations if needed.
- Verification: Unit tests for model creation; run schema integrity against dev DB.
- Risks: Missing indexes causing slow comment lookup; migration ordering issues.

## Stage 2 – Comment retrieval & serialization
- Dependencies: Stage 1.
- Changes: Create service helper to load comments for a request (oldest-first) and serialize with author usernames.
- Verification: Service tests ensuring ordering, filtering out soft-deleted comments.
- Risks: N+1 query patterns; leaking deleted comments.

## Stage 3 – Posting endpoint + validation
- Dependencies: Stage 1.
- Changes: Add POST `/requests/{id}/comments` endpoint that enforces auth, validates body length, creates comment, and returns both JSON metadata and rendered HTML snippet (via template partial).
- Verification: Route tests covering success, validation failures, and permission denials.
- Risks: Duplicated validation logic, race conditions when returning HTML.

## Stage 4 – UI integration & vanilla JS
- Dependencies: Stage 2, Stage 3, existing request detail template.
- Changes: Render comments list + form on request detail page; add small JS module to intercept form submit, call endpoint, inject HTML without reload, and handle error fallback.
- Verification: Manual browser test, optional JS unit (if feasible), ensure graceful degradation when JS disabled (full reload path still works).
- Risks: JS errors breaking other parts of the page; inconsistent markup between partial and full render.

## Stage 5 – Moderation hooks & documentation
- Dependencies: Prior stages complete.
- Changes: Add soft-delete admin capability and note in docs (optional if time), mention commenting in README/features, update feature summary doc.
- Verification: Manual admin flow test if implemented; ensure docs reflect behavior.
- Risks: Scope creep if moderation becomes complex; documentation lag.
