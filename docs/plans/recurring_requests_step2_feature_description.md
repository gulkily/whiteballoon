# Recurring Requests · Step 2 Feature Description

**Problem**: House managers currently have to remember and retype recurring chores or meeting requests. They need a way to predefine templates that automatically generate drafts (or fully publish) on a schedule so the community sees consistent reminders without manual copy/paste.

**User stories**
- As a house manager, I want to create a recurring request template listing description, contact info, cadence, and whether it should land as a draft or an auto-published request so that routine needs stay on schedule.
- As a manager reviewing drafts, I want incoming recurring copies to appear in my drafts list with clear metadata (source template, due date) so I can verify, edit, and publish them quickly.
- As a manager configuring auto-published templates, I want confidence that the system posts them exactly once per interval and logs that fact so I can audit activity or pause a template if needed.
- As a community member, I want recurring posts to follow the normal request feed/pin behaviors so the experience feels consistent regardless of whether a request was generated manually or via template.

**Core requirements**
1. Provide a UI (likely under Requests or Settings) to create/manage recurring request templates capturing: title/description, contact email override, recurrence interval (daily/weekly/custom cron-like), next run timestamp, and delivery mode (`draft` vs `publish`).
2. Implement an in-app scheduler loop that runs inside the server process, wakes up on a configurable cadence, and clones templates whose next-run time has passed—creating drafts assigned to the template owner or publishing immediately if configured.
3. Track execution metadata per template (last run time, next run time, status, error note) and display it in the management UI so managers can pause/resume templates or diagnose failures.
4. Ensure generated requests integrate with existing systems: still respect `HelpRequest` schema, pinned limits, notifications, and the drafts surface introduced earlier.
5. Provide safeguards: prevent duplicate runs (idempotency per template + time window), allow pausing/deleting templates, and surface basic activity logs for accountability.

**Shared component inventory**
- `app/models.py` / new template model/table: define `RecurringRequestTemplate` storing recurrence settings, owner, and status metadata. Possibly reuse SQLModel conventions.
- `app/routes/ui/requests.py` or a new management route + templates under `templates/requests/` or `templates/settings/` to list/create/update templates.
- `static/js/request-feed.js` (read-only integration) plus a new JS module for template management forms if inline editing is needed.
- Scheduler hook (e.g., `app/scheduler.py` or inside `app/main.py`) to launch an async/background task that evaluates templates without external cron.
- Existing draft APIs in `app/modules/requests/routes.py` and services to create `draft` or `open` help requests; reuse them for template cloning.

**User flow**
1. Manager opens the Recurring Requests settings page, clicks “New template,” and fills out description, cadence (e.g., weekly Monday 9am), and chooses Draft or Auto-publish.
2. Scheduler runs inside the app, sees the template’s `next_run_at` <= now, and clones the help request via the existing draft/publish APIs while recording `last_run_at`.
3. If the template uses Draft mode, the new copy appears in the manager’s drafts list with a badge linking back to the template; the manager reviews edits and publishes like any other draft.
4. If Auto-publish, the cloned request appears immediately in the public feed (with normal notifications/pinning rules). Managers can pause/delete the template if it needs changes.
5. Managers can view template history showing last execution and upcoming schedule; pausing stops the scheduler from enqueuing new clones until resumed.

**Success criteria**
- Managers can create at least one recurring template and see it generate drafts on time without manual interaction.
- Templates configured for Auto-publish create visible help requests exactly once per intended interval (no duplicates within the same window).
- Managers can pause or delete a template and the scheduler stops generating copies within one interval.
- Generated requests reuse the same IDs/status pipeline (draft vs open) and surface in the existing UI components with no special-case layouts.
