# Step 2 – Feature Description: Comment Insights Dashboard

## Problem
Admin stakeholders cannot browse the LLM-generated comment insights without running CLI commands. We need a dedicated admin UI surface that lists recent runs and lets admins inspect analyses inline, so they can spot trends and audit tags quickly.

## User Stories
- As an admin, I want a `/admin/comment-insights` page that shows all recent LLM runs with provider/model metadata so I can see what processed recently.
- As an admin, I want to click a run and view each comment’s summary/tags plus a link to the original request so I can verify context.
- As an admin, I want lightweight filters (snapshot label, provider) so I can narrow to specific campaigns without exporting data.

## Core Requirements
- Add new admin UI route + template that consumes the existing `/api/admin/comment-insights` endpoints.
- Display run list with columns: snapshot_label, provider, model, started_at (friendly), completed/total batches, and a CTA to load analyses.
- Inline run detail table (HTMX/JS) that loads analyses via the API and shows summary, tags, link to comment/request.
- Basic filters (snapshot label text, provider dropdown) backed by API query parameters.
- No data mutation; read-only view for admins only.

## User Flow
1. Admin visits `/admin/comment-insights`.
2. Page loads recent runs (default 20) and shows filter inputs.
3. Admin selects a run (click row or button) → HTMX request fetches analyses table below that row.
4. Within the analyses table, each row links to the original request/comment (new tab).
5. Admin adjusts filters to refresh the run list as needed.

## Success Criteria
- Page loads in under 2 seconds with at least 10 runs populated.
- Clicking a run loads analyses in <2 seconds without reloading the whole page.
- Filters correctly narrow the run list (verified via manual tests).
- No errors or regressions in existing admin routes.
