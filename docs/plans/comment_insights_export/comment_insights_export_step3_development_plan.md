# Step 3 – Development Plan: Comment Insights CSV Export

## Stage 1 – API export endpoint
- Add router method `/admin/comment-insights/runs/{run_id}/export` (admin-only) that streams CSV using `StreamingResponse`.
- Reuse existing service to fetch analyses; serialize rows with `csv.writer` (quote tags arrays as JSON strings).
- Verify via curl that the CSV downloads and includes headers.

## Stage 2 – UI button + wiring
- Add “Export CSV” button in run detail partial; link to the new endpoint (target `_blank` or `download` attribute).
- Ensure button only shows when analyses are available.

## Stage 3 – Polish & limits
- Set proper filename (`comment-insights-<run_id>.csv`), content type `text/csv`.
- Add friendly error message if export fails.
- Document the feature in Step 4 log once verified.
