# Dedalus Prompt Logging – Step 2 Feature Description

## Problem
Admins cannot inspect the prompts, responses, or tool calls involved in Dedalus interactions, leaving them blind to what data we share and how agents reach conclusions.

## User Stories
- As an admin, I want to see every prompt we send to Dedalus so I can verify sensitive data stays within policy.
- As an admin, I want to review Dedalus responses and tool outputs to judge accuracy before acting.
- As an admin, I want an activity log with filters and exports so I can audit past interactions quickly.

## Core Requirements
- Capture each Dedalus invocation with timestamp, initiating user, target entity (request/comment), prompt text, model, and context hash.
- Persist logs inside a dedicated SQLite file (e.g., `storage/dedalus_logs.db`) isolated from the primary DB for easier rotation and export.
- Append Dedalus responses, tool-call metadata (name, arguments, result), and final status to the same log entry.
- Expose an admin control-panel view (“Dedalus Activity”) listing recent entries with expand/collapse details, filter by entity/user/date, and CSV export.
- Provide retention controls: configurable max age (default 30 days) and a manual “Purge older entries” button.
- Redact secrets automatically (API keys, bearer tokens, etc.) before persistence or display.

## User Flow
1. Admin triggers a Dedalus-assisted action (e.g., summary). Backend logs outbound payload metadata into the SQLite log DB with a correlation ID.
2. Dedalus responds (with optional tool calls); backend updates the same entry with response text, tool call traces, and status.
3. Admin opens the control panel’s “Dedalus Activity” page, which queries the log DB, shows entries chronologically, and allows detail inspection/export.
4. Retention job (or manual purge) deletes rows older than the configured window from the SQLite file.

## Success Criteria
- Every Dedalus run appears in the activity view within seconds, showing prompt, response, and tool-call list.
- Sensitive fields confirmed redacted via manual spot-check.
- Configurable retention works: entries older than the window disappear after purge job/manual action.
- Admins can download a CSV of filtered results for offline review.
