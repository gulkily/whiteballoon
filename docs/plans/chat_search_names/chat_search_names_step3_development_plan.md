# Chat Search Names – Step 3 Development Plan

## Stage 1 – Data plumbing
- **Goal**: Provide display name + profile link metadata to the chat search results template.
- **Dependencies**: Existing request detail context, `request_comment_service.serialize_comment` payloads, and chat search view.
- **Changes**: Ensure `comment_display_names` (or similar map) is available to the template for search results; no new DB queries required because the map already exists from the comment list.
- **Verification**: Manually load a request with Signal personas and confirm the template receives both display-name + username.
- **Risks**: None—reuses existing data.

## Stage 2 – Template + CSS tweaks
- **Goal**: Update the chat search list items to mimic the comment list identity layout.
- **Dependencies**: Stage 1 data available.
- **Changes**: Swap the leading `@username` with conditional display name markup, add tooltips, ensure the link points to `/people/<username>`, and keep the timestamp jump link.
- **Verification**: Manual UI check on desktop/mobile ensuring names link to profiles while timestamps still jump to comments.
- **Risks**: Minimal; watch for layout regressions.
