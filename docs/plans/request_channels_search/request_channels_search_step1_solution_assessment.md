# Request Channels Search — Step 1 Solution Assessment

## Problem
Request Channels search is local-only, so investors can only find requests already present in the initial page load instead of querying the full dataset with filters/permissions applied server-side.

## Options
- **Option A – Extend existing `/api/requests` with search params**
  - Pros: Reuses established serialization + auth checks; minimal new surface area; keeps parity with other request listings.
  - Cons: Requires threading new query params through existing index cache logic and may impact current consumers if performance changes.
- **Option B – Dedicated `/api/request-channels/search` endpoint**
  - Pros: Purpose-built for channel workspace (status/pinned filters, unread counts) and keeps additional logic isolated from general request feed.
  - Cons: Duplicates serialization unless carefully refactored; new endpoint to secure/monitor; potential drift from canonical request payloads.

## Recommendation
Choose **Option A**: extend `/api/requests` (or its helper) with lightweight search + status filters so we keep one canonical query path, ensuring shared caching, permissions, and serialization without fragmenting the request model.
