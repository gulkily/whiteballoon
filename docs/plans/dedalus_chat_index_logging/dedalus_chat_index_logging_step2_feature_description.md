# Dedalus Chat Index Logging — Step 2 Feature Description

## Problem
When `wb chat index` runs with `--llm`, Dedalus processes comment text but nothing is logged in `/admin/dedalus/logs`. Admins can’t audit prompts/responses, identify failures, or measure usage for these runs.

## User Stories
- As an admin, I can view chat-index LLM runs in `/admin/dedalus/logs` with the request/comment context to troubleshoot or audit usage.
- As an operator, running `wb chat index --llm` automatically records a Dedalus log entry without extra flags, so I don’t need to instrument anything manually.
- As a product owner, I can see when LLM classification fails (status/error) via the log viewer.

## Core Requirements
- Wrap Dedalus-powered classifier calls inside `request_chat_index.py` with `start_logged_run`/`finalize_logged_run`, including metadata (request ID, comment ID, model) and the prompt/response (redacted).
- If classification touches additional tools (e.g., embedding or heuristics), include tool call entries via the logging helper.
- Ensure logging failures don’t break the CLI (keep existing try/except behavior).
- Show these runs in `/admin/dedalus/logs` alongside existing entries (no extra UI changes expected).

## Shared Component Inventory
- `app/tools/request_chat_index.py`: houses the LLM classifier that needs logging.
- `app/dedalus/logging.py` + `app/dedalus/log_store.py`: existing logging helpers used by `/admin/dedalus/logs`.
- UI: `/admin/dedalus/logs` page already renders log entries; no template changes unless new metadata is added.

## User Flow
1. Operator runs `wb chat index --request-id 123 --llm --llm-comment 456`.
2. For each comment that hits the LLM, the classifier calls `start_logged_run(...)`, executes the prompt, and `finalize_logged_run(...)` with success/error details.
3. Admin visits `/admin/dedalus/logs` and sees entries labeled “chat-index” (or similar) with the prompt summary and any errors.

## Success Criteria
- Running `wb chat index --llm ...` produces new entries in `/admin/dedalus/logs` with request/comment IDs and status.
- Logging failures don’t stop the CLI; they’re caught and only warn in logs.
- No behavior change for `wb chat index` when `--llm` isn’t used.
