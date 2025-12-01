# Profile Comments Titles – Step 2 Feature Description

## Problem
Profile comment pages repeat the same Signal-imported request title for dozens of entries, making it hard to scan or differentiate comments quickly.

## User stories
- As an admin reviewing a Signal persona, I want consecutive comments from the same request to visually group together so I’m not overwhelmed by identical titles.
- As an admin, I want to keep pagination and chronological order intact so I can still step through comment history page by page.
- As an operator, I want grouped sections to clearly show the request title/ID once so I never lose context for which thread the comments belong to.

## Core requirements
1. Group consecutive comments on the profile comments index by request ID/title: render the title once as a header before the list of entries.
2. Each comment still shows body, timestamp, scope chip, and request link (the link can move to the group header to reduce duplication if desired).
3. Pagination logic remains unchanged—ordering stays newest-first, page size constant, and group headers reset per page.
4. Works for both native profiles and Signal personas using the existing permissions model (admin-only access).

## User flow
1. Admin opens `/people/<username>/comments`.
2. Comments appear in reverse chronological order. When the underlying request changes, a new group header appears with the request title and link; all comments belonging to that request sit beneath it.
3. Admin pages through history as needed; each page may show multiple groups depending on content.

## Success criteria
- Repeated Signal titles no longer clutter every row; only one heading per consecutive block.
- Comments retain their context (scope badge, timestamp, body) within each group.
- Pagination continues to work identically to the pre-change behavior.
- Inline snippet on `/people/<username>` and other templates still render correctly (no regressions).
