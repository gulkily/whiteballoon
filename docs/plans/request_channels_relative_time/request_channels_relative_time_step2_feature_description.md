# Request Channels Relative Time

## Problem
The request channels sidebar shows long-form hour counts like "431 hours ago," which is hard to scan and inconsistent with the app’s standard `friendly_time` formatting.

## User stories
- As a member, I want channel timestamps to roll up to days/weeks and calendar dates so the sidebar stays readable at a glance.
- As a maintainer, I want one shared client-side formatter to avoid each view inventing its own relative-time rules.

## Core requirements
- Use a shared client-side relative-time formatter for request channel timestamps.
- Match the existing `friendly_time` behavior for thresholds (minutes, hours, days, weeks, then date/time).
- Avoid hour-only displays beyond 24 hours.
- Handle future timestamps gracefully ("in X" or date) without crashing.
- Keep existing timestamp data attributes so no API schema changes are required.

## Shared component inventory
- `app/routes/ui/helpers.py` `friendly_time` filter (server-side canonical behavior) — should remain the source of truth for formatting rules.
- `static/js/request-channels.js` `updateRelativeTime` — will reuse/extend the shared formatter instead of custom logic.
- `static/js/realtime-status.js` `formatRelativeTime` — candidate for reuse of the shared formatter to prevent drift.
- `static/js/request-chat-search.js` absolute timestamp rendering — no change planned unless future standardization is requested.

## Simple user flow
1. User opens `/requests/channels`.
2. The sidebar renders each channel’s updated timestamp using the shared formatter.
3. Older items display days/weeks or a formatted date instead of large hour counts.

## Success criteria
- No channel timestamp shows hour counts above 24 (e.g., "431 hours ago").
- `/requests/channels` timestamps follow the same thresholds as `friendly_time`.
- The formatter is shared (single function) rather than duplicated per view.
