# Dedalus Comment LLM Logging — Step 3 Development Plan

## Stage 1: Identify logging hook points
- **Goal**: Map where in `app/tools/comment_llm_processing.py` we need to start/finalize Dedalus log runs when `provider == "dedalus"`.
- **Dependencies**: Step 2 doc approved.
- **Changes**: Read through `DedalusBatchLLMClient` usage and the execution loop (`main()` function) to confirm the exact scope (per batch) and what metadata is available (snapshot label, run_id, batch index, prompt string).
- **Verification**: Confirm notes by cross-referencing existing log usage (`request_chat_index.py`). No code changes yet.
- **Risks**: None—discovery step.

## Stage 2: Wrap batch executions with Dedalus logging
- **Goal**: Instrument batch execution loop so each Dedalus batch logs start/end with metadata.
- **Dependencies**: Stage 1.
- **Changes**:
  - Import `app.dedalus.logging as dedalus_logging` into `app/tools/comment_llm_processing.py`.
  - Before calling `client.analyze_batch` (and only if provider == "dedalus"), call `start_logged_run` with fields: `user_id="cli"`, `entity_type="comment_llm_batch"`, `entity_id=f"{run_id}:{idx}"`, `model=ns.model`, `prompt` as the built prompt or a summarized string, `context_hash` derived from batch comment IDs.
  - After the call, finalize with `status="success"` and the serialized response; on exceptions, finalize with `status="error"` and re-raise so existing retry/interrupt logic works.
  - Ensure the logging wrapper respects retries (i.e., a failed attempt finalizes with error before retrying, and a successful retry starts a fresh logged run).
- **Verification**: Run `./wb chat llm --snapshot-label test --limit 1 --batch-size 1 --execute --provider mock` to ensure mock path unaffected; optionally run with dedalus provider in mockable way (or dry-run) to verify logging calls via unit-level inspection/log tail.
- **Risks**: Logging errors must not crash the CLI (helpers already swallow exceptions); ensure prompt redaction avoids leaking sensitive text.

## Stage 3: Persist representative prompt summary for logs
- **Goal**: Provide a concise, redactable prompt string for logging instead of the full multi-comment prompt.
- **Dependencies**: Stage 2 instrumentation in place.
- **Changes**:
  - Create helper to produce a prompt summary (snapshot label, batch id, comment count, comment ids) without raw bodies.
  - Use this summary when starting the logged run; optionally attach the actual prompt in `context_hash` or metadata if safe.
- **Verification**: Print the generated summary during development (or inspect by running CLI with `--json-summary` and ensuring no bodies leak).
- **Risks**: Summary must still be useful for admins; avoid including PII or large blobs.

## Stage 4: Manual verification + cleanup
- **Goal**: Confirm Dedalus logs appear and document verification steps.
- **Dependencies**: Stage 2-3 complete.
- **Changes**:
  - Run `./wb chat llm ... --provider dedalus --execute` (or simulate if API unavailable) and verify `/admin/dedalus/logs` (or the SQLite log store) shows the new entries with correct metadata.
  - Update Step 4 implementation summary doc.
  - Ensure no stray prints or debug logs remain.
- **Verification**: Tail the Dedalus log DB (`storage/dedalus_logs.db`) or the admin UI to see the new row; confirm error path by interrupting a batch and seeing status updated.
- **Risks**: Access to actual Dedalus API may be limited; fallback is to inspect the log DB directly.

