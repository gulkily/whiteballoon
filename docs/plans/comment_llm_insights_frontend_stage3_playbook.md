# Stage 3 – Implementation Playbook: Comment LLM Insights Frontend

## Capability 1 – Admin Insights Dashboard
1. Add `/admin/comment-insights` route + template (HTMX shell). Display run list table (snapshot_label, provider, model, started/completed batches). [~60 LoC]
2. Hook table to `/api/admin/comment-insights/runs?limit=50` via HTMX GET; show spinner + error state. [~40 LoC]
3. Add filter form (snapshot label text + provider select) that triggers HTMX request. Backend: extend API to accept optional filter params. [~50 LoC]
   - Verification: manual load confirms runs appear, filters work, API logs expected queries.

## Capability 2 – Run Detail & Comment Drilldown
1. Add HTMX endpoint `/admin/comment-insights/runs/{run_id}` returning analyses table (summary, tags, comment link). [~70 LoC]
2. Embed trigger in run list rows (click loads detail card below row). [~30 LoC]
3. Include “view original comment” link (opens request detail in new tab) + “show summary” modal/tooltip. [~40 LoC]
4. Add search/filter within analyses table (client-side filter by tag keyword). [~30 LoC JS]
   - Verification: run detail loads under 2s, comment links open correct page, search filters entries live.

## Capability 3 – Inline Preview Hook (request detail)
1. Annotate comment list template to show an icon/badge when API says analysis exists (call new helper from service). [~40 LoC]
2. Badge link: either inline tooltip (pulls summary via `/api/admin/comment-insights/comments/{id}`) or link to admin run detail with anchor. [~30 LoC]
3. Hide badge behind feature flag or admin check initially. [~15 LoC]
   - Verification: comments with analyses show indicator; clicking reveals summary or navigates to dashboard.

## Capability 4 – CSV Export
1. Add API route `/api/admin/comment-insights/runs/{id}/export` returning CSV (same data as table). [~40 LoC]
2. Add button on run detail panel that hits the endpoint (download attribute). [~20 LoC]
   - Verification: download contains headers + all rows; open in spreadsheet matches UI.

## Capability 5 – Feature Flag + Filtering for user-facing labels
1. Introduce config flag (`COMMENT_INSIGHTS_PUBLIC`) surfaced to templates. [~20 LoC]
2. When flag on, show tags in request detail (read-only) and optionally expose filter controls (query param to API). [~40 LoC]
3. Ensure admin dashboard can filter by tag/resource/request type (extend API query). [~60 LoC]
   - Verification: toggling flag hides/shows tags, filters return narrowed results; no errors when flag off.

## Instrumentation & Ops
- Log API usage for runs/analyses endpoints (counts, error rates) to monitor adoption.
- Ensure SQLite WAL file is included in backups.
- Document feature flag behavior + how to enable in staging/prod.
