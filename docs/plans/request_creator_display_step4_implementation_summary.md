## Stage 1 – Expose creator metadata
- `RequestResponse` now includes an optional `created_by_username`, populated via a shared `load_creator_usernames` helper that batches user lookups for each request list.
- Server-rendered views reuse the helper during serialization so half-auth and fully authenticated sessions receive the same enriched payloads.

### Testing
- Manual: Pending — need to hit `/api/requests` and confirm username values appear for recent and older requests.

## Stage 2 – Render creator in request cards
- Updated `templates/requests/partials/item.html` to surface the creator name in the leading header cluster with a friendly fallback label.
- Applied structural markup changes only, leaving visual polish for the client-side styling pass to keep parity with upcoming updates.

### Testing
- Manual: Pending — load both the full dashboard and half-auth pending view to confirm names render without breaking alignment.

## Stage 3 – Align client rendering and styles
- Brought the dynamic request renderer in `static/js/request-feed.js` in sync with the server template, including the creator label and updated header structure.
- Tweaked request card styles to support the new layout, adding lead container spacing and a distinct visual treatment for the creator name.

### Testing
- Manual: Pending — submit a request and confirm the live refresh shows the creator label with consistent styling; spot-check on small screens for wrapping.
