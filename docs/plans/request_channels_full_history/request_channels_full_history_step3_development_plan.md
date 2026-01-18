# Request Channels Full History — Step 3 Development Plan

1. **Newest-slice API hook**
   - **Goal**: Allow the workspace to request the latest N comments without loading the legacy page.
   - **Changes**: Add a helper in `app/routes/ui/__init__.py` (or a tiny API route) to return the most recent `limit` comments plus an offset/token for fetching older slices; reuse request-detail serialization to avoid duplication.
   - **Verification**: Manual `curl`/browser check hitting the new endpoint and confirming the JSON/HTML includes the newest comments.
   - **Risks**: Need to guard payload size and ensure permissions match the legacy view.

2. **Client optimistic confirmation**
   - **Goal**: Keep the optimistic “Sending…” bubble and swap it with the server response instead of wiping the whole log.
   - **Changes**: Refactor `static/js/request-channels.js` send flow so POST success updates just the last message (or appends the canonical markup) and only triggers a full reload when necessary. Track comment IDs to differentiate the optimistic placeholder from confirmed data.
   - **Verification**: Manual test posting in short and long threads ensuring the optimistic bubble transitions to the final message without scroll jumps.
   - **Risks**: Need to handle failure states cleanly so placeholders don’t stick around; ensure presence/unread metrics still refresh.

3. **Jump-to-newest indicator + scroll preservation**
   - **Goal**: When the user isn’t near the bottom, show a floating pill that scrolls to the newest comment; while reloading/adding older slices, preserve scroll position.
   - **Changes**: Track scroll position, add a sticky “New activity — Jump to latest” button, wire it to `scrollTo`, and restore scroll offsets when older slices are appended. Add CSS for the pill.
   - **Verification**: Manual test scrolling up, receiving/sending messages, seeing the pill appear, and confirming clicking it jumps to the bottom and hides it; ensure scroll doesn’t reset when loading earlier content.
   - **Risks**: Edge cases with mobile/short viewports; must debounce scroll listeners to avoid performance issues.

4. **Load earlier history control**
   - **Goal**: Provide a way to fetch older slices on demand so the workspace can browse entire threads.
   - **Changes**: Add a “Load earlier” button or infinite-scroll trigger that calls the newest-slice API with appropriate cursor/offset to prepend older comments; update the DOM without disturbing current view.
   - **Verification**: Manual test loading multiple slices, ensuring order stays chronological and no duplicates appear.
   - **Risks**: Cursor math, race conditions with concurrent loads, and ensuring we don’t exceed memory limits.

5. **Polish & QA**
   - **Goal**: Validate the full experience (optimistic send, indicator, load earlier) across desktop/mobile and confirm accessibility cues (live regions, focus management) remain intact.
   - **Changes**: Update announcer text if needed, ensure the new pill and loads have screen-reader labels, and document the new behavior.
   - **Verification**: Manual smoke across at least one long thread; optionally add regression notes to the implementation summary.
   - **Risks**: Missing a11y details or regressions in presence/unread counts; ensure tests or manual scripts cover them.
