# Request Channels Search — Step 2 Feature Description

## Problem
Request Channels search only filters the preloaded DOM list, so admins/demo hosts can’t discover older or filtered requests without leaving the workspace. We need server-backed search that respects permissions and mirrors request feed filters.

## User stories
- As a founder demoing channels, I want search to pull any request by title/description so I can quickly open historical asks mid-call.
- As an admin, I want status/pinned filters to combine with search results from the full dataset so that prioritization workflows stay accurate.
- As a member, I want the workspace search to respect my visibility scope so I don’t see private requests I can’t access elsewhere.
- As an operator, I want the client to avoid spamming the API while typing so logs stay clean and predictable.

## Core requirements
- Add search + status/pinned filters to the canonical `/api/requests` (or shared helper) for authenticated viewers, reusing existing serialization.
- Include unread + comment counts in API responses so the workspace list stays consistent after remote fetches.
- Update the Request Channels UI to debounce text input, call the API, and replace/append list items while showing a loading state.
- Maintain local filtering for already-fetched items so switching filters doesn’t always hit the network when data is fresh.
- Preserve optimistic badge/selection behaviors when the list refreshes with remote results.

## Shared component inventory
- Request list serialization (`RequestResponse` + `_serialize_requests` helper) → extend to accept search/status filters and optional unread metadata.
- Channel list UI (`request-channel` buttons) → reuse existing markup; only the data source changes.
- Presence/unread services (`request_channel_reads`, `_load_channel_comment_counts`) → reuse to calculate counts for newly fetched ids.

## User flow
1. Viewer types in the search box or toggles a filter; UI shows “Searching…” state.
2. JS debounces input (e.g., 300 ms) and calls `/api/requests?search=<query>&status=open&include_pinned=1` (parameters TBD).
3. Server returns filtered request payloads plus counts; client rebuilds the list and preserves the active channel (if still present) or selects the first result.
4. Presence/unread polling continues using the new ids; local filters fall back to cached results when the query hasn’t changed.

## Success criteria
- Search returns results outside the initial preload within 1 second for typical datasets (<1k requests).
- API only fires after debounce and when parameters change, preventing unnecessary load (verified via network panel).
- Channel list reflects server results, including unread badges, and keeps the active chat open when still available.
- Users with limited scopes never see requests they can’t access elsewhere (parity with `/requests`).
