# Step 3 – Development Plan: Comment Insights Inline Indicators

## Stage 1 – Feature flag + service hook
- Add `COMMENT_INSIGHTS_INDICATOR` config flag + template context helper.
- Extend `comment_llm_insights_service` with a `has_analysis(comment_id)` helper (maybe cached per request).
- Verify flag toggles behavior in dev.

## Stage 2 – Template badge
- Update request detail comment template to render badge/icon when helper says analysis exists and flag enabled.
- Style with existing badge classes; include data attributes for JS hook.

## Stage 3 – Tooltip/modal fetcher
- Add small JS module to listen for badge clicks, fetch `/api/admin/comment-insights/comments/{id}`, and render summary/tags in a tooltip or inline card.
- Handle errors + loading state.

## Stage 4 – Dashboard link bridge
- Add “Open in dashboard” link from tooltip to `/admin/comment-insights` with query params (snapshot/run) or direct anchor.
- Ensure deep-link loads the run detail (reuse JS from dashboard).

## Stage 5 – QA + flag rollout docs
- Document flag in DEV_CHEATSHEET + README.
- Manual regression on request detail view (flag on/off).
