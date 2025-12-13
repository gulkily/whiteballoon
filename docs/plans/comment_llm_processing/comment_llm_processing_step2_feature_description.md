# Step 2 – Feature Description: Comment LLM Processing

## Problem
We need a dependable way to process the ~7.3k existing help-request comments through an LLM so we can summarize themes and opportunities without breaking rate limits, overspending, or losing per-comment traceability.

## User Stories
- As a product analyst, I want to batch-run comments through an LLM so I can discover recurring user pains in hours instead of weeks.
- As a support lead, I want each AI-generated insight to cite original comment IDs so I can follow up with request owners when needed.
- As an engineer, I want a predictable job that can restart mid-run so I can operate it safely even if an upstream outage occurs.
- As an operations manager, I want cost estimates before processing begins so I can approve or pause the run.

## Core Requirements
- Provide a batched processing job (5–15 comments per request) with deterministic pagination over the existing comment dataset.
- Persist structured outputs that retain per-comment references and LLM summaries/labels.
- Support retrying failed batches without duplicating results for comments already processed.
- Expose real-time or near-real-time progress (e.g., batch counts, estimated cost, failures) to operators.
- Enforce configurable rate limiting and cost ceilings to keep API usage under control.

## User Flow
1. Operator selects the comment dataset snapshot plus batch size/rate-limit settings and starts the job.
2. System estimates token/cost usage based on selected parameters and requires operator confirmation.
3. Job iterates over comments deterministically, submitting each batch to the LLM and storing structured responses tied to comment IDs.
4. Monitoring surface (CLI or admin UI log) updates progress, cost consumed, and any failed batches in real time.
5. Operator reviews stored outputs to consume insights or retry flagged batches if needed.

## Success Criteria
- 100% of existing help-request comments processed with no duplicates and <1% manual retries.
- Total LLM spend stays within the configured budget envelope for the run.
- Operators can view progress and cost within 30 seconds of starting the job.
- Each stored insight links back to its original comment ID for auditing.
