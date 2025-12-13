# Stage 0 – Problem Framing: Comment LLM Insights Frontend

## Problem Statement
Product and ops teams need to browse the LLM-generated comment summaries/tags directly in the web UI to spot trends and drill into individual help requests, but the current data is only accessible via admin-only APIs/SQLite, forcing engineers to run CLI commands for every question.

## Pain Points
- No UI affordance to inspect the 7k+ comment analyses already generated; stakeholders rely on ad-hoc JSON dumps.
- Manual CLI queries make it hard to compare runs or see metadata (provider, spend) in context when triaging requests.
- Support/ops cannot verify that tags match the original comment without developer assistance.

## Success Metrics
- Admin UI page lists recent LLM runs and their completion progress (≥1 run visible within 5 seconds of load).
- Operators can filter comment insights by request/comment and export the table (CSV) without CLI.
- Feedback cycle under 30 seconds from click → seeing tags/summary inline.

## Guardrails
- Scope limited to read-only surfaces inside the existing admin UI (no public exposure yet).
- Reuse the new SQLite store + APIs; no additional LLM processing or schema changes.
- Deliver incremental UI (list → detail) so we can ship partial value if timelines tighten.
