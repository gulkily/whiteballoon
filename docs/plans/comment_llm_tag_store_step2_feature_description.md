# Step 2 – Feature Description: Comment LLM Tag Store

## Problem
Front-end experiences need to surface the LLM-generated summaries/tags for each request comment, but the current JSONL artifacts are not queryable or safe to expose directly. We need an idempotent SQLite store of runs/analyses so UI code can read them via normal DB access patterns.

## User Stories
- As a product manager, I want to browse recent LLM insights in the admin UI so I can spot themes quickly without parsing JSON files.
- As a frontend engineer, I want a stable database table of comment analyses so I can render tags inline with help requests without additional ETL steps.
- As an operator, I want to rerun the CLI and have only new/changed analyses inserted so I can recover from failures without duplicating rows.

## Core Requirements
- Introduce a dedicated SQLite database (e.g., `data/comment_llm_insights.db`) with tables for runs and per-comment analyses, co-located with other app data files.
- Extend the CLI to write each batch’s metadata + analysis rows into the SQLite store idempotently (skip/overwrite controls match existing JSONL behavior).
- Provide a lightweight ingestion/read service inside the app that can fetch analyses by comment ID or run label for frontend use.
- Keep file-based artifacts (JSONL/JSON) for backfill/debug while ensuring the DB is the primary source for UI queries.
- Do not block or slow existing processing runs; DB writes should piggyback on the existing batch loop.

## User Flow
1. Operator runs `wb comment-llm ... --execute` to process comments.
2. For each batch, the CLI persists summaries/tags into the SQLite database under `data/comment_llm_insights.db` (insert-or-replace semantics) and still writes JSONL for backup.
3. Backend service exposes a query (e.g., by comment_id or run label) that the frontend can hit.
4. Frontend components fetch and display tags/summary chips based on the stored analyses.

## Success Criteria
- CLI run completes with the new SQLite DB populated (verified by counting rows) without regressing performance (>5% overhead per batch).
- UI/API consumers can query analyses for a given comment ID and receive consistent data on two consecutive runs (idempotency).
- JSONL artifacts remain intact for at least one full run to support rollback/backfill.
