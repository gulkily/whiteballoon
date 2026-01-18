# Step 2 – Feature Description: Comment Insights Inline Indicators

## Problem
Admins reviewing request detail pages can’t tell which comments already have LLM tags without opening the separate dashboard. They need inline cues (and quick access to the analyses) to verify context while reading the original comments.

## User Stories
- As an admin, I want to see a badge next to comments that have LLM insights so I know which ones were processed.
- As an admin, I want to click that badge to view the summary/tags (or jump to the full dashboard) without losing my place on the request page.

## Core Requirements
- Comment list template should show an icon/badge for comments with stored analyses (admins only, behind feature flag initially).
- Badge click fetches the analysis via existing API endpoint and displays a tooltip/modal (or links to the dashboard run) with summary + tags.
- Feature flag (`COMMENT_INSIGHTS_INDICATOR`) controls visibility so we can soft launch.
- Non-admin users see nothing (until we deliberately expand scope).

## User Flow
1. Admin opens a help request detail page.
2. Comments with analyses show “Insights” badge (maybe tooltip) next to metadata.
3. Clicking badge fetches `/api/admin/comment-insights/comments/{id}` and either shows a tooltip or opens the dashboard filtered to the run.
4. Closing the tooltip or navigating back returns to the same scroll position.

## Success Criteria
- Badges render only for comments with analyses and disappear when flag off.
- Fetching summary takes <1s and shows friendly error if unavailable.
- No layout shift/regressions on request detail page.
