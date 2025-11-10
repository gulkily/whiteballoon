## Problem
Request detail pages don’t allow members to discuss the request, so clarifications, updates, or encouragement have to happen elsewhere.

## User Stories
- As a member, I want to post a comment on a request page so I can clarify details or offer support.
- As a member, I want to see existing comments in chronological order so I understand the full conversation.
- As a member, I want to add a comment without the page reloading so I don’t lose my place on long threads.
- As a viewer without full permissions, I want to be prevented from commenting so request discussions stay secure.

## Core Requirements
- Create a `request_comments` data model tied to `help_requests` and `users`, storing body, timestamps, and soft-deletion flags.
- Update the request detail route/template to display comments beneath the request content, sorted oldest-first, with author info and timestamps.
- Add a comment form for authenticated, fully approved users; POST endpoint returns both HTML snippet and JSON payload so vanilla JS can append it without reload.
- Include basic validation (non-empty body, max length) and show inline error states if validation fails, with a graceful fallback to full-page reload.
- Ensure permission checks prevent half-authenticated sessions or unauthenticated visitors from posting, while still showing public comments to readers.

## User Flow
1. Member opens a request detail page and scrolls to the comments section.
2. The page shows existing comments plus a form (if the user can comment) with a textarea and submit button.
3. On submit, a small JS snippet sends the form via `fetch`; on success it injects the rendered comment HTML at the end of the list and clears the form. On error it surfaces validation messages or falls back to reloading.
4. Other readers refreshing the page see the new comment via the server-rendered list.

## Success Criteria
- Authenticated, fully approved members can submit comments that persist to the database and appear immediately in the UI without full reload.
- Validation errors (empty body, too long) display inline and prevent writes.
- Comments stored server-side render consistently on page load, even if JS fails.
- Unauthorized users never see the comment form and receive a 401/403 if they attempt to POST directly.
- Implementation uses existing stack (FastAPI + SQLModel + vanilla JS) without introducing HTMX or new frameworks.
