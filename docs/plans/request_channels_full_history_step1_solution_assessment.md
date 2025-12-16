# Request Channels Full History — Step 1 Solution Assessment

## Problem
In large threads, posting a new comment from the Request Channels workspace refreshes only the first page of the request detail context, so the freshly added message falls outside the returned slice. The optimistic “Sending…” bubble disappears but the real message isn’t visible, confusing hosts during demos.

## Scenarios
- **Viewer on latest messages**: Most common case; after sending a reply the panel reloads page 1 instead of newest page, so the new message disappears completely.
- **Viewer scrolled upward**: Expectation is to keep context steady, but today the reload snaps back to page 1/scroll top and still omits the fresh message, forcing a switch to legacy view.
- **Long-standing threads with > page-size comments**: Even without posting, entering the channel shows only the earliest comments, so workspace users never see recent activity.
- **Short threads (< page size)**: Behaves correctly—new messages remain visible—highlighting the inconsistency compared to larger discussions.
- **Mobile/narrow view**: Losing the newly sent message makes it hard to confirm delivery because the composer takes more vertical space; users often assume it failed.

## Options
- **Option A – Fetch all comments for channel view**
  - Pros: Guarantees newly added messages appear immediately regardless of thread size; simplest mental model.
  - Cons: Large requests could render hundreds of comments at once, increasing payload size and slowing the workspace.
- **Option B – Latest slice + optimistic confirmation + “jump to newest” pill**
  - Pros: Optimistic bubble stays in place, confirmed message replaces it without wiping scroll; a floating badge invites users to scroll down when new activity lands while they’re mid-thread; keeps payload bounded by fetching only the newest N entries.
  - Cons: Requires JS changes (tracking scroll state, showing the pill) plus a backend tweak to return the newest slice; still need a strategy to browse older history (e.g., “Load earlier”).
- **Option C – Reuse pagination but jump to newest page after posting**
  - Pros: Minimal backend change; respects existing pagination settings.
  - Cons: Still splits the conversation, and jumping users to another page in the workspace could be jarring; doesn’t solve the “stay in place” scenario.

## Recommendation
Adopt **Option B**: keep the channel response limited to the latest N comments but enhance the client so optimistic messages persist until the server-confirmed version replaces them, and show a “Jump to latest” pill when the user isn’t at the bottom. This lets hosts verify their new messages instantly without losing their place, while keeping payload sizes manageable.
