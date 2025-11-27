# Feed Spacing & Card Hierarchy Refresh — Step 2 Feature Description

## Problem
Request cards sit back-to-back, metadata floats inconsistently (status on the left, timestamp on the far right), and primary actions blend with secondary ones. The feed feels dense and tiring to scan, especially on mobile.

## User Stories
- As a visitor, I want help requests presented with breathing room so I can skim and decide which need to open.
- As a helper, I want metadata (status, timestamp, requester) grouped predictably so I don’t hunt around each card.
- As a maintainer, I want the call-to-action buttons to convey clear hierarchy without modifying backend logic.

## Core Requirements
- Introduce consistent vertical spacing between sections/cards using shared CSS tokens.
- Rework each card’s header meta strip: align requester, status, and timestamp on a single row mirroring the detail view.
- Differentiate primary vs secondary actions (e.g., “Share a request” vs “Send Welcome”) via color/weight tweaks.
- Ensure changes respect responsive layouts and don’t regress the new detail-page styling.

## User Flow
1. User arrives on the feed and sees evenly spaced cards with a readable hero section.
2. Each card displays requester, status badge, and timestamp in a unified strip.
3. Primary actions stand out while secondary actions remain accessible but subdued.

## Success Criteria
- Vertical rhythm applies consistently (desktop + mobile) without manual overrides.
- Meta strip alignment matches the detail page pattern; timestamp link still works.
- Primary action buttons stand out; secondary actions remain discoverable.
- Manual smoke test confirms no layout collisions with long copy or status badges.
