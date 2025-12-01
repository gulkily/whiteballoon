# Realtime Status Feedback for Admin Actions

## Problem
Admin-triggered operations (Push/Pull, Dedalus connection tests, etc.) run asynchronously today without consistent realtime or polling feedback, forcing admins to guess whether work is still pending or failed.

## User Stories
- As an admin, I want to see a live status indicator whenever I trigger a backend process so I know it is actively running.
- As an admin, I want the UI to refresh status automatically (SSE/WebSocket when available, polling fallback) so I do not have to click refresh.
- As an admin, I want each status component to surface success, failure, or warning details so I can decide the next action immediately.
- As an admin, I want historical timestamps for the start and completion of each action so I can report on recent work without leaving the page.

## Core Requirements
- Provide a shared UI pattern (component + CSS + copy) describing how to display "in progress", "success", "failed", and "warning" states beside any admin action button.
- Backend endpoints that kick off long-running work must respond immediately with a job identifier and initial status payload.
- Frontend must subscribe to realtime updates (server-sent events or websockets) and fall back to polling every ≤3 seconds until a terminal state.
- Status payloads must include current phase, progress percent (if known), timestamp, and optional error message so messages remain structured.
- Every asynchronous admin action must log completion with job id, timestamps, result, and human-readable summary for later surfacing.

## User Flow
1. Admin clicks an action button (e.g., Push, Pull, Test Dedalus connection).
2. Frontend POSTs to the action endpoint; backend enqueues work and returns `{job_id, initial_status}`.
3. Frontend renders the standardized status component in "in progress" state and initiates realtime subscription (SSE/WebSocket) with the job id; falls back to polling if the realtime channel fails.
4. Backend emits status updates keyed by `job_id`; frontend updates the component on each message until it receives a terminal state (`success`, `failed`, or `warning`).
5. On completion, frontend displays the final status, description, timestamps, and exposes a "View details" link if extra logs exist; backend records the job outcome for auditing.

## Success Criteria
- 100% of admin-triggered asynchronous operations render the standardized status component within 0.5s of button click.
- Status indicators update at least every 3s while work is running (or faster if realtime events arrive).
- Final state, summary message, and timestamps persist in logs and are queryable via API.
- Error states display actionable text (error message or remediation hint) without inspecting server logs.
- QA demo: trigger Push, Pull, and Dedalus test actions and observe live transitions from pending → in-progress → success/failure without manual refresh.
