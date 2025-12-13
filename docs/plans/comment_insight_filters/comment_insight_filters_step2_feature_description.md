## Problem
The “Comment insights” panel lists tags and urgency chips, but clicking them does nothing. Users expect chips to filter the comment list, and they want sharable URLs that preserve the selected filters.

## User Stories
- As a member, I want to click a tag (e.g., “housing”) and instantly see only the comments matching that tag.
- As a moderator, I want the filter state reflected in the URL so I can send `...?insight_tag=housing&sentiment=positive` to teammates and have it load pre-filtered.
- As a reader returning to the request, I want the filters I bookmarked to reapply automatically without extra clicks.

## Core Requirements
- Extend the request-detail context so each serialized comment includes its LLM tags/urgency/sentiment (minimal payload: arrays of tag slugs + normalized urgency/sentiment strings).
- Enhance the “Comment insights” card chips to act as toggles; selection state updates the comment list in place (hide unmatched comments) and syncs to query parameters.
- On initial page load, parse any `insight_tag`, `insight_resource`, `insight_request`, `insight_urgency`, or `insight_sentiment` query params and apply the same filtering server-side (so the correct subset renders even before JS runs).
- Support multiple filters at once (e.g., one resource tag plus an urgency).
- Provide a clear indicator/count of how many comments match and a reset action to clear filters.

## Shared Component Inventory
- `app/routes/ui/__init__.py`: augment `_build_request_detail_context` to include insight tags per comment and read filter query params.
- `templates/requests/detail.html`: update the insights card markup to show active state, counts, and a reset link; add headings/badges for current filters.
- `templates/requests/partials/comment.html` / `partials/comment_card.html`: add data attributes/classes for tags so JS can hide/show comments efficiently.
- New JS (e.g., `static/js/comment-insight-filters.js`) to handle chip clicks, filtering, and `history.pushState` to sync the URL.

## Simple User Flow
1. User clicks the “housing” chip → comments filter immediately, chips show active state, URL updates with `?insight_resource=housing`.
2. User copies the URL and sends it; teammate opens it and sees the same filtered comment list.
3. User hits “Reset filters” to show all comments again.

## Success Criteria
- Clicking chips filters comments without reloading, and the URL reflects the state.
- Reloading the page (or opening a shared URL) applies filters server-side even before JS kicks in.
- Filtering works with multiple chips and can be cleared easily.
- No performance regression when tags are absent (filters hide automatically).
