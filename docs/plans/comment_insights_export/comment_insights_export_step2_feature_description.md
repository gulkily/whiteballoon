# Step 2 – Feature Description: Comment Insights CSV Export

## Problem
Admins often need to move the LLM insight data into spreadsheets or share it with other tools. Right now the only way is to copy/paste from the UI or JSON, which is slow and error-prone. We need a one-click CSV export per run.

## User Stories
- As an admin, I want an “Export CSV” button on the run detail panel so I can download all analyses for a run as a spreadsheet.
- As an analyst, I want the CSV to include run metadata plus per-comment fields (summary, tags, comment ID, request ID, timestamps) so I can pivot/filter offline.

## Core Requirements
- Add API endpoint (admin-only) that streams the analyses for a given run as CSV (UTF-8, headers included).
- Include key columns: run_id, snapshot_label, provider, model, comment_id, help_request_id, summary, resource_tags, request_tags, audience, residency_stage, location, urgency, sentiment, tags, notes, recorded_at.
- Add “Export CSV” button in the run detail UI that triggers file download.
- Keep response time acceptable (<3s for ~200 rows).

## User Flow
1. Admin opens `/admin/comment-insights` and expands a run.
2. Clicks “Export CSV”.
3. Browser downloads `comment_insights_<run_id>.csv`.

## Success Criteria
- Downloaded file opens cleanly in Excel/Sheets and matches the on-screen data.
- Non-admins cannot access the export endpoint.
