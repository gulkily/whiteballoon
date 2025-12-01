# Dedalus Prompt Logging – Step 3 Development Plan

## Stage 1 – Define Log Schema + SQLite Helper
- **Goal:** Establish the dedicated SQLite database (`storage/dedalus_logs.db`) and schema (tables for runs + tool calls).
- **Changes:** Create helper module (e.g., `app/dedalus/log_store.py`) that ensures DB file exists, runs migrations (via simple CREATE TABLE IF NOT EXISTS), and exposes insert/update/query primitives. Tables capture run metadata (id, timestamp, user_id, entity_type/id, model, prompt, status) plus tool calls (run_id, tool_name, arguments, output).
- **Verification:** Run helper in shell to create DB, inspect schema via `sqlite3 .schema`.
- **Risks:** File permission issues; ensure storage dir exists and is gitignored.

## Stage 2 – Instrument Dedalus Client Wrapper
- **Goal:** Log outbound prompts and inbound responses/tool calls using the helper.
- **Changes:** Wrap existing Dedalus client invocation (likely in `app/dedalus/client.py` or similar) to record a run before sending the request, then update it afterward with response text, tool traces, duration, and status. Redact secrets in prompt/response.
- **Verification:** Trigger sample Dedalus call via CLI (existing “Dedalus connectivity” tool) and confirm entries appear in SQLite with both prompt and response. Manually inspect DB.
- **Risks:** Logging code must not crash the main flow; guard failures and continue.

## Stage 3 – Admin UI & API Endpoint
- **Goal:** Provide “Dedalus Activity” view in control panel that reads from SQLite and displays logs.
- **Changes:** Add FastAPI route (e.g., `/admin/dedalus/logs`) returning paginated/filterable data from log helper. Create corresponding template/React/HTMX view in admin UI showing list with expand/collapse detail (prompt, response, tool calls) plus filters (date range, user, entity type). Include CSV export endpoint reusing same queries.
- **Verification:** Load admin page, ensure entries render and filters work; download CSV and confirm contents.
- **Risks:** Query performance (use LIMIT/OFFSET); ensure UI guards large payloads.

## Stage 4 – Retention + Purge Controls
- **Goal:** Enforce configurable retention window and manual purge option.
- **Changes:** Add config value (e.g., `DEDALUS_LOG_RETENTION_DAYS`). Implement CLI/management command or scheduled job (hook into existing cron) that deletes rows older than window. Add admin button “Purge older than X days” calling backend endpoint which runs deletion and reports count.
- **Verification:** Insert older rows via SQL, run purge job/button, confirm rows removed. Validate config default (30 days).
- **Risks:** Unintended deletion; wrap in transaction and confirm before commit.

## Stage 5 – Documentation & Ops Notes
- **Goal:** Document setup and maintenance.
- **Changes:** Update `docs/dedalus/meeting_brief.md` or new ops doc explaining log location, retention config, and privacy guarantees. Note backup considerations for SQLite file.
- **Verification:** Peer review doc; ensure instructions let another dev find logs.
- **Risks:** None significant.
