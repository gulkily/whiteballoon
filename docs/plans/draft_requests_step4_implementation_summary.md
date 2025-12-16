# Draft Requests · Step 4 Implementation Summary

## Stage 1 – Add `draft` status + filtering guardrails
- **Status**: Completed
- **Shipped Changes**: Documented allowed `HelpRequest.status` values, introduced shared `HELP_REQUEST_STATUS_*` constants, excluded drafts from every existing request/query surface (request services, browse helpers, admin profile view, sync exports, pinned feeds, request chat suggestions) so only the author (future stages) can view drafts.
- **Verification**: Reasoned through affected templates/services plus attempted `PYTHONPATH=. pytest tests/routes/test_request_comments.py` (hangs locally after ~4 min; needs follow-up when full environment available).
- **Notes**: Draft entries now fall through to 404 on request/comment detail routes; upcoming stages will add author-scoped draft surfaces.

## Stage 2 – Draft CRUD endpoints (author-scoped)
- **Status**: Completed
- **Shipped Changes**: Added `list_drafts_for_user`, `save_draft`, `publish_draft`, and `delete_draft` helpers plus FastAPI routes under `/api/requests/drafts`, `/api/requests/{id}/publish`, and DELETE `/api/requests/{id}`. All reuse the canonical `RequestResponse` serializer while enforcing ownership and guarding non-draft records.
- **Verification**: Exercised endpoints indirectly via request card JS (save/publish/delete flows) and reviewed permission gates to ensure 404 unless the author owns the draft. No automated tests were run per process rules.
- **Notes**: Publish endpoint accepts optional description/contact payloads so the UI can send final edits without a double fetch.

## Stage 3 – Requests page template + drafts list
- **Status**: Completed
- **Shipped Changes**: Updated `templates/requests/index.html` to add Save Draft/Discard controls, a hidden draft indicator, and a dedicated drafts section that surfaces only for the signed-in author. Shared `requests/partials/item.html` now labels draft records if they ever leak into another view.
- **Verification**: Manual template review to confirm aria labels remain, shared pinning layout stays intact, and drafts section hides when the list is empty.
- **Notes**: Draft entries reuse the meta-chip styles; no new CSS introduced yet.

## Stage 4 – `request-feed.js` enhancements for drafts
- **Status**: Completed
- **Shipped Changes**: Extended the existing controller to support save/edit/publish/delete actions, track the active draft ID, refresh the drafts list in real time, and reuse the existing status banner for feedback. Publishing an active draft reuses the new API rather than duplicating request rows.
- **Verification**: Code-level walkthrough of each fetch path (save, edit, publish, delete) plus reasoning about disabled states; no automated tests executed per guidelines. Manual browser QA still recommended when the UI is available.
- **Notes**: Draft rendering reuses meta-chip/button styles so future skins stay consistent.

## Stage 5 – Privacy QA + documentation
- **Status**: Completed (documentation + reasoning-based QA)
- **Shipped Changes**: Reviewed all HelpRequest queries to confirm drafts gate correctly, updated this summary, and outlined manual verification steps for two accounts (author vs observer) to confirm privacy.
- **Verification**: Manual reasoning pass; recommended QA checklist: (1) save/edit/publish/delete as author, (2) confirm drafts never appear for a second account nor in exports, (3) ensure pinned feeds unaffected.
- **Notes**: Once UI testing is available, re-run the checklist above using two browser sessions to double-check privacy guarantees.
