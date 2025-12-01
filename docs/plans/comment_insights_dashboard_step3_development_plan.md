# Step 3 – Development Plan: Comment Insights Dashboard

## Stage 1 – Route + template shell
- **Goal**: Create `/admin/comment-insights` FastAPI handler + Jinja template with HTMX placeholders and basic admin gating.
- **Dependencies**: Existing admin auth helpers, templates.
- **Changes**: Add route method to `app/routes/ui/admin.py`, new template `templates/admin/comment_insights.html`, wire nav link.
- **Verification**: Hit the page as admin → empty shell renders; non-admin denied.
- **Risks**: None beyond template wiring.

## Stage 2 – Run list integration
- **Goal**: Populate run list table via API (HTMX) with filters.
- **Changes**: Add HTMX endpoint returning partial HTML for run list; create small JS/HTMX snippet; extend API to accept filters.
- **Verification**: Manual test: initial load shows runs; filter inputs trigger HTMX request updating table.
- **Risks**: API pagination/filter mismatches.

## Stage 3 – Run detail + analyses table
- **Goal**: Load per-run analyses inline when clicking a row.
- **Changes**: Add HTMX endpoint returning analyses partial; template JS to insert detail row; include summary/tags and request link.
- **Verification**: Click run -> analyses appear; multiple runs toggle independently; links open request page.
- **Risks**: Large runs causing long load; consider limiting to first N rows.

## Stage 4 – Polish + tests
- **Goal**: Add friendly timestamps, empty states, basic CSS; ensure filter parameters persist.
- **Changes**: Template tweaks, helper functions, maybe small CSS chunk.
- **Verification**: Manual regression: empty DB shows “no runs”; refresh maintains filters; lint/tests pass.
- **Risks**: None (UI polish).
