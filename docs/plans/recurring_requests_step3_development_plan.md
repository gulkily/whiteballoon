# Recurring Requests · Step 3 Development Plan

**Step 3 reminder**: Break work into atomic stages (~≤1 hr / ≤50 LOC) with clear goals, dependencies, verification steps (manual OK), risks, and highlight each canonical component touched. Flag stages that still feel large so they can be split before coding.

## Stage 1 – Template schema + persistence
- **Goal**: Introduce a `RecurringRequestTemplate` SQLModel + migration to store owner, description, cadence, mode, and scheduling metadata (next run, last run, paused flag).
- **Dependencies**: None.
- **Changes**: Update `app/models.py` (new table), add alembic/SQLModel migration, and create basic CRUD helpers (`app/services/recurring_template_service.py`) for create/update/list/delete. Fields: `created_by_user_id`, `title`, `description`, `contact_email_override`, `delivery_mode` (`draft`/`publish`), `interval_minutes` (or cron spec), `next_run_at`, `last_run_at`, `paused`, `last_error`.
- **Verification**: Manual migration run against dev DB plus `python -m app.shell` snippet to create/list templates.
- **Risks**: Interval math may evolve (cron vs minutes); start with minutes + optional anchor timestamp.

## Stage 2 – Scheduler loop infrastructure
- **Goal**: Launch an in-app background task that periodically scans templates and triggers due runs without external cron.
- **Dependencies**: Stage 1 schema/services.
- **Changes**: Add scheduler bootstrap (e.g., `app/scheduler.py`) invoked from `app/main.py` on app start, using asyncio/ThreadPool to run `check_recurring_templates()` every N minutes. Ensure it respects app shutdown, uses DB session per tick, and logs activity via `logging`.
- **Verification**: Manual run (`uvicorn` locally) with a short interval template; confirm logs show scheduler firing.
- **Risks**: Multiple workers duplicating; mitigate by row-level locking or `next_run_at` update inside transaction.

## Stage 3 – Template execution + cloning service
- **Goal**: Implement the actual cloning logic that turns a template into a draft or published request.
- **Dependencies**: Stages 1–2.
- **Changes**: Add service (`recurring_template_executor.py`) that, for due templates, creates either a `draft` via existing draft APIs or publishes (respecting `HelpRequest` status). Update `next_run_at` using template interval, set `last_run_at`, and write failure reason if creation fails. Integrate with Stage 2 scheduler.
- **Verification**: Manual invocation via shell/test harness to ensure drafts show up for template owner; confirm auto-publish populates `/api/requests` feed.
- **Risks**: Duplicate runs if two scheduler ticks overlap; ensure execution uses DB transaction + `next_run_at` update before release.

## Stage 4 – Manager UI for template CRUD
- **Goal**: Provide a settings/requests subpage for house managers to create, edit, pause, and delete recurring templates.
- **Dependencies**: Stage 1 data + Stage 3 execution metadata.
- **Changes**: Add route (e.g., `/requests/recurring`) under `app/routes/ui/requests.py` or new module, templates under `templates/requests/recurring.html`, and simple forms (HTML + minimal JS) to manage templates. Display fields: cadence, mode, next run, last run/error; include actions to pause/resume.
- **Verification**: Navigate in browser, create template, pause/resume, and observe DB updates.
- **Risks**: Form UX may need JS for dynamic fields (interval vs cron). Keep scope to simple inputs first.

## Stage 5 – Draft integration + activity logging
- **Goal**: Surface metadata on generated drafts and log executions for audit.
- **Dependencies**: Stage 3 executor.
- **Changes**: Tag created drafts/requests with a `request_attribute` linking back to template ID, display a badge in drafts list (“From template Foo”), and log each run in new table or existing logging module. Update `static/js/request-feed.js` + templates to show the badge.
- **Verification**: Create template that generates draft; confirm drafts list shows reference and logs record run.
- **Risks**: Too much UI clutter; keep badge subtle.

## Stage 6 – QA + documentation
- **Goal**: Verify end-to-end (draft vs auto publish) and document scheduler behavior.
- **Dependencies**: Prior stages.
- **Changes**: Manual QA checklist for: creating templates, scheduler-run drafts, auto-publish, pause/resume, duplicate protection. Update Step 4 summary + README/Feature docs with scheduler instructions.
- **Verification**: QA notes + Step 4 doc update.
- **Risks**: Scheduler timing tests tricky locally; consider reducing interval temporarily during QA.
