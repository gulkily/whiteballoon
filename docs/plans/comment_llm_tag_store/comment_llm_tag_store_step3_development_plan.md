# Step 3 – Development Plan: Comment LLM Tag Store

## Stage 1 – SQLite schema + access layer
- **Dependencies**: Step 2 requirements; existing comment analysis data structures
- **Changes**: Define `data/comment_llm_insights.db` with tables for runs (run_id, snapshot_label, provider, model, started_at, completed_batches, total_batches) and analyses (comment_id PK, run_id FK, help_request_id, summary, resource_tags, request_tags, audience, residency_stage, location, location_precision, urgency, sentiment, tags, notes, recorded_at). Add a small Python access module to open connections and run migrations (create tables if missing).
- **Verification**: Unit-level script that initializes the DB and shows the tables exist. Confirm rerunning init is idempotent (no errors).
- **Risks**: Schema drift if CLI + consumer disagree; concurrent writes if multiple runs overlap (keep single-writer assumption).

## Stage 2 – CLI writer integration
- **Dependencies**: Stage 1 DB helpers
- **Changes**: Extend `app/tools/comment_llm_processing.py` batch loop to insert/replace run + analysis rows via the new access layer, in addition to JSONL writes. Ensure `--include-processed` toggles overwrite behavior. Record how many rows were written/skipped per batch for logging.
- **Verification**: Run CLI with `--provider mock` to process a few comments and query the SQLite DB (using a quick helper) to confirm rows exist and idempotent reruns skip unless `--include-processed` is set.
- **Risks**: Performance hit if inserts aren’t batched; sqlite file locking failures if operator opens it in a UI mid-run.

## Stage 3 – Backend read service
- **Dependencies**: Stage 2 DB data available
- **Changes**: Create a lightweight service (e.g., `app/services/comment_llm_insights.py`) that reads analyses by comment_id/run_id. Make it safe to call from FastAPI routes or background tasks. Optionally expose a CLI command to dump recent runs for admins.
- **Verification**: Write a small FastAPI dependency or script that queries the DB for comment IDs known to have analyses and ensure the returned data matches the CLI output.
- **Risks**: Connection lifecycle management (ensure connections close); reading stale data if multiple processes run on different hosts (acceptable for now since the DB is local).

## Stage 4 – Frontend integration entry point
- **Dependencies**: Stage 3 service in place
- **Changes**: Add a placeholder API handler or template helper that the frontend can call (even if it just returns JSON for now). Document how UI should access the new store. No major UI work yet—just the backend endpoint to unblock future stories.
- **Verification**: Hit the new endpoint via curl or tests to confirm it returns analyses for a sample comment.
- **Risks**: Over-fetching if the endpoint isn’t scoped; ensure it gracefully handles comments with no analyses.

## Stage 5 – Backfill/import utility
- **Dependencies**: Stages 1-3 complete
- **Changes**: Write a script (or CLI flag) that replays existing JSONL artifacts into the SQLite DB so historical runs are present without rerunning the LLM. Support dry-run mode to inspect counts.
- **Verification**: Remove/rename the DB, run the importer, and confirm row counts match the JSONL lines.
- **Risks**: Duplicate entries if importer isn’t idempotent; mismatch between legacy schema and new DB schema.
