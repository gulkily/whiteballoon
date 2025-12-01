# Request Detail Pages — Step 2 Feature Description

## Problem
The request feed only exposes summaries; individual requests lack dedicated URLs, making it hard to share, revisit, or layer tracking information over time.

## User Stories
- As a requester, I want a shareable page for my request so I can send it to neighbors without exposing the entire feed.
- As a helper, I want to view a request’s full context on a focused page so I can understand the need and respond effectively.
- As an administrator, I want canonical request URLs so future tracking tools can annotate and monitor request progress.

## Core Requirements
- Provide a server-rendered detail page at `/requests/<id>` using existing FastAPI + Jinja patterns.
- Render the same fields as the feed (status, description, creator details, timestamps) with room for future metadata.
- Respect access rules (e.g., read-only for half-auth users, hide private data) consistent with the feed.
- Add navigation affordances back to the feed and expose the canonical link for sharing (e.g., copy button or clear URL display).
- Reuse existing request serialization logic where possible to avoid duplication.

## User Flow
1. User visits `/requests/<id>` from the feed or via a shared link.
2. Server loads the request, applies authorization checks, and renders a detail template.
3. Page displays request information and actions (e.g., mark complete) consistent with the user’s permissions.
4. User can navigate back to the main feed or copy the URL for sharing.

## Success Criteria
- Every request has a routable, server-rendered detail view with stable URLs.
- The detail page mirrors feed permissions and does not expose additional data to unauthorized viewers.
- Users can easily navigate back to the feed and the canonical link is obvious for sharing.
- New route covered by manual smoke test (and automated tests where feasible).
