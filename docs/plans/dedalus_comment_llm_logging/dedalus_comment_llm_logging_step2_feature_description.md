# Dedalus Comment LLM Logging — Step 2 Feature Description

## Problem
Dedalus-powered comment batch runs executed via `wb chat llm --provider dedalus` are invisible in `/admin/dedalus/logs`, preventing admins from auditing prompts/responses or correlating spends with stored analyses.

## User Stories
- As an admin, I want each executed Dedalus batch to appear in the log timeline so I can review when comment analyses ran.
- As an operator running `wb chat llm`, I want Dedalus logging to happen automatically so I don’t need extra flags or scripts.
- As a reviewer triaging outages, I want log entries to record the snapshot label, provider, and batch index so I can match them to saved outputs.

## Core Requirements
- Each Dedalus API invocation triggered by the comment LLM runner must wrap the prompt/response with `start_logged_run` / `finalize_logged_run`.
- Logged runs must capture contextual metadata: user (`cli`), entity type (`comment_llm_batch`), entity id (batch index or run id), provider/model, and a representative prompt summary.
- Errors should finalize the log entry with `status="error"` while allowing execution retries or shutdown logic to continue.
- Logging must not spam per-comment entries; batches are the atomic unit.
- Optional providers (e.g., `mock`) should bypass logging cleanly.

## Shared Component Inventory
- **Dedalus log store + admin UI** (`app/dedalus/log_store.py`, `/admin/dedalus/logs`): reuse the existing logging helpers; no new schema.
- **Comment LLM insights DB / promotion queue**: read-only reference; no changes required.
- **CLI wrapper (`wb.py`)**: continues to invoke `app.tools.comment_llm_processing`; no interface change.

## User Flow
1. Operator runs `wb chat llm ... --provider dedalus --execute`.
2. The CLI builds batches and, before each `client.analyze_batch`, calls `start_logged_run(...)` with batch metadata.
3. After the Dedalus client returns (or errors), the CLI finalizes the log with status + response snippet.
4. Admin visits `/admin/dedalus/logs` and sees entries labeled with snapshot/run/batch info that link back to stored outputs.

## Success Criteria
- Executing at least one batch with `--provider dedalus` produces a new entry in `/admin/dedalus/logs` whose metadata references the snapshot label and batch index.
- Interrupting or hitting an exception still finalizes the log row with `status="error"` or `"interrupted"`.
- Running the CLI with `--provider mock` produces no Dedalus log rows and the CLI behavior is unchanged.

