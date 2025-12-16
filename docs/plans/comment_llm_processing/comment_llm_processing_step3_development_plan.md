# Step 3 – Development Plan: Comment LLM Processing

## Stage 1 – Data access & deterministic batching scaffolding
- **Dependencies**: Existing comment models and read access; feature description
- **Changes**: CLI/worker entry point taking dataset snapshot parameters; deterministic pagination over comments with stable ordering; dry-run mode that only counts tokens/costs
- **Verification**: Run dry-run against staging data and confirm comment counts + estimated cost match spreadsheet math
- **Risks**: Pagination drift if new comments appear mid-run; mis-estimated token sizes

## Stage 2 – LLM prompt + batching executor
- **Dependencies**: Stage 1 scaffolding
- **Changes**: Prompt template (system + user) tuned for hacker house rubrics; batching logic (5–15 comments) with retry/backoff; hooks for cost tracking per batch
- **Verification**: Run against <3 test batches, confirm responses include per-comment IDs and structured JSON; simulate API failure to observe retry
- **Risks**: Prompt overflow; inconsistent JSON emitted by the model

## Stage 3 – Persistence + idempotency guardrails
- **Dependencies**: Stage 2 executor output contract
- **Changes**: Storage table or document model for batch results (per-comment summaries, labels, metadata); write-once semantics; resume logic skipping already-processed comments
- **Verification**: Process overlapping runs and ensure second run skips persisted comments; inspect stored rows for schema correctness
- **Risks**: Duplicate writes if idempotency key not unique; schema mismatch with prompt fields

## Stage 4 – Monitoring, operator controls, and cost ceilings
- **Dependencies**: Stage 3 persistence + cost hooks
- **Changes**: Operator-facing progress surface (CLI stdout or admin dashboard) showing batches processed, failures, spend-to-date vs ceiling; configuration for max batches per minute and max spend; graceful stop when thresholds hit
- **Verification**: Run job with low ceilings to trigger stop; observe logs/UI updates; check failure notifications
- **Risks**: Race conditions when updating shared counters; confusing UX if stop conditions fire silently

## Stage 5 – Classification review + adjustments
- **Dependencies**: Stages 2-4 in place to produce data
- **Changes**: Sample stored outputs, verify hacker-house rubric coverage; tweak prompt instructions or post-processing to ensure required fields (resource type, request type, location, urgency, etc.) are populated
- **Verification**: Manually audit ≥50 comments across resource/request categories; confirm taxonomy coverage and adjust as needed
- **Risks**: Drift between prompt expectations and reality; reprocessing cost if taxonomy changes later

## Classification Rubric (current draft)
- **Resource Types**: housing/beds, house amenities (workspace, workshops, events), funding/offers (stipends, shared meals), logistics (travel groups, airport pickups), guides/tools
- **Request Types**: housing availability, roommate matching, event collaboration, shared transportation, visa/legal help, local orientation/onboarding, emotional support
- **Community Signals**: audience flag (residents, hosts, adjacent collaborators such as sponsors/organizers), residency stage (pre-arrival, on-site, post-residency), whether it targets a specific house or the broader network
- **Location Granularity**: explicit house names, neighborhoods/cities, travel corridors between houses, plus precision flag (exact vs general)
- **Engagement & Urgency**: urgent openings/waitlists, capacity thresholds, requests nearing deadlines, sentiment cues indicating stress vs informational posts
