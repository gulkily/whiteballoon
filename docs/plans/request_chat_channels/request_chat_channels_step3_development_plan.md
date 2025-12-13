# Request Chat Channels – Step 3 Development Plan

## Stage 1 – Workspace shell + routing
- **Goal**: Add `/requests/channels` route with dual-pane scaffold (empty channel list + chat pane placeholder) wired to existing request index store.
- **Dependencies**: Request index data provider (`RequestListStore`), layout primitives.
- **Changes**: New page component + route entry; fetch channel list via existing index API; add feature flag gate; include reminder that channel list reuses canonical store.
- **Verification**: Load route manually, confirm left/right panes render with sample placeholders and respect feature flag.
- **Risks**: Layout regressions on smaller screens; forgetting to gate route for non-beta users.

## Stage 2 – Channel list presentation
- **Goal**: Render request rows as channel list with unread badges, priority icons, and quick filter atop the existing index data.
- **Dependencies**: Stage 1 shell; `RequestListStore`; badge icon assets.
- **Changes**: Virtualized list component; integrate quick filter/search; derive unread counts from comment metadata; reuse `RequestDetailHeader` chips for priority/assignee summary.
- **Verification**: Manually confirm scrolling, filtering, unread badge updates on mock data; keyboard focus works.
- **Risks**: Performance issues with many requests; inconsistent unread counting logic.

## Stage 3 – Chat pane log rendering
- **Goal**: Display chronological comments with Slack-style bubbles, avatars, timestamps, and sticky composer wrapper.
- **Dependencies**: Comment fetch API; `CommentCard`, `IdentityChip`, `CommentComposer` components.
- **Changes**: New chat log component using existing comment endpoints; extend `CommentCard` styles for chat bubbles; wrap `CommentComposer` inside sticky footer and add optimistic send handling.
- **Verification**: Select channel → comments load and scroll to newest; send message and see optimistic bubble before server response.
- **Risks**: Scroll jitter when new messages arrive; visual inconsistencies with canonical comment components.

## Stage 4 – Presence + typing indicators
- **Goal**: Show online/typing state per channel using `RealtimePresenceStore`.
- **Dependencies**: Stage 2 list + Stage 3 chat; existing presence service topics.
- **Changes**: Subscribe to presence topics keyed by request ID; update channel rows with presence dots; show typing indicator in composer header; throttle updates to avoid flicker.
- **Verification**: Simulate multiple browser sessions; observe presence + typing states update within a few seconds.
- **Risks**: Over-subscribing to channels causes load; stale presence data confusing users.

## Stage 5 – Deep links + unread sync
- **Goal**: Map legacy request URLs into the workspace and keep unread counts consistent between list and chat pane.
- **Dependencies**: Stage 1 routing; Stage 2 list; Stage 3 chat log.
- **Changes**: Add router hook to intercept `/requests/{id}` and redirect to `/requests/channels#{id}` or state param; mark channel read when scrolled to bottom; sync read state back to backend.
- **Verification**: Open legacy links, ensure workspace focuses correct channel; unread badge clears after viewing; QA sample of 20 URLs.
- **Risks**: Redirect loops; unread state race conditions causing missed notifications.

## Stage 6 – Polish + accessibility
- **Goal**: Tighten keyboard navigation, announce new messages, and ensure responsive behavior.
- **Dependencies**: All prior stages complete.
- **Changes**: Add keyboard shortcuts for channel switching; ARIA live regions for new chat messages; responsive CSS adjustments for narrower widths.
- **Verification**: Run keyboard-only session; screen reader announces updates; resize window to confirm layout stability.
- **Risks**: Accessibility regressions if announcements spam; shortcut conflicts with existing app combos.
