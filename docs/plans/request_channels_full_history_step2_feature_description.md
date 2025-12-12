# Request Channels Full History — Step 2 Feature Description

## Problem
Large request threads currently load only the oldest page in the Request Channels workspace, so new messages vanish after posting and historic context is inaccessible without opening the legacy page.

## User stories
- As a host demoing a long channel, I want my newly sent reply to remain visible immediately so I can confirm it landed.
- As a contributor reviewing older context, I want to stay at my current scroll position even when others post new replies, but get a clear signal when fresh comments arrive.
- As an operator, I need a bounded payload so I can load the workspace on slower networks without pulling thousands of comments.

## Core requirements
- Server-side: expose an API/fragment that returns the newest N comments (configurable) for a channel plus metadata to fetch older slices on demand.
- Client: keep the optimistic “Sending…” bubble until the server confirms the message, then replace it in-place without rerendering the entire list.
- Client: detect when the user isn’t near the bottom and show a “Jump to newest” pill whenever new comments arrive (from self or others); clicking it scrolls to bottom and hides the pill.
- Client: preserve scroll position when refreshing the list or loading older history chunks.
- Provide a “Load earlier messages” affordance so users can browse older slices without leaving the workspace.

## Shared component inventory
- Channel chat panel (`channel_chat.html`, `static/js/request-channels.js`) – extend to support lazy loading, optimistic confirmation, and the “jump to newest” chip.
- Comment promotion modal & composer already reused; ensure added UI respects existing CSS utilities.
- Request detail serialization – add an entry point that returns the newest comments, with an API contract similar to the existing comments pagination.

## User flow
1. User opens `/requests/channels?channel=123`; client requests the newest slice (e.g., last 50 comments) and renders them.
2. User scrolls upward; workspace loads earlier slices lazily when the user requests them.
3. User types a reply and clicks Send; optimistic bubble appears at bottom, then swaps with confirmed comment when POST returns. If user scrolled away, a “New message — Jump to newest” chip appears.
4. If another participant posts while the user is reading older content, the chip appears; clicking it scrolls to bottom and clears the indicator.

## Success criteria
- New comments stay visible after posting regardless of thread size; optimistic bubble never disappears without showing the confirmed message.
- Jump-to-newest chip appears only when the user is not near the bottom and clears when the user scrolls down or clicks it.
- Loading older slices does not block posting or presence; payload size for initial load stays under the configured limit (e.g., ≤50 comments).
- Users report no more “message disappeared” confusion during demos; legacy page is no longer required to confirm posts.
