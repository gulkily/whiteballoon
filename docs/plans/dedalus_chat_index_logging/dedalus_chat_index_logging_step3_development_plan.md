# Dedalus Chat Index Logging — Step 3 Development Plan

## Stage 1 – Wire logging helpers into classifier
- **Goal**: Wrap the Dedalus LLM classifier inside `request_chat_index.py` with `start_logged_run` / `finalize_logged_run`.
- **Changes**: Import `app.dedalus.logging` in `app/tools/request_chat_index.py`. When the classifier is instantiated (LLM mode), capture context (request/comment IDs, model) and log each call. Include prompt text + hashed context; redact if necessary. Ensure tool outputs record success or errors.
- **Verification**: Run `wb chat index --request-id <id> --llm --llm-comment <cid>` with Dedalus/LLM enabled; confirm logs are persisted via a quick SQL query or by loading `/admin/dedalus/logs`.
- **Risks**: Logging failures must not abort the CLI; keep try/except wrappers.

## Stage 2 – Surface metadata & polish
- **Goal**: Improve log readability.
- **Changes**: Add structured labels (e.g., `entity_type='request_chat'`, `entity_id=<request_id>`) and include the classifier model name. Consider grouping comment IDs in the log context. No UI change if log already renders these fields.
- **Verification**: Check log entries at `/admin/dedalus/logs` and ensure fields are populated.
- **Risks**: Accidentally logging raw/unredacted data; rely on existing `redact_text` helper.

## Stage 3 – Documentation & testing notes
- **Goal**: Update docs/cheatsheet if mention of logging is helpful; document manual verification steps.
- **Changes**: Note in README or admin docs that `wb chat index --llm` now logs to Dedalus activity. Capture manual test results in Step 4 summary.
- **Verification**: Markdown review; show sample log entries.
- **Risks**: Doc drift minimal.
