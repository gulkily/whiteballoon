# Recurring Request Archiving — Step 3 Development Plan

## Stage 1 – Backend bulk archive helper
- **Goal**: Provide a service method + admin route that archives every published request linked to a recurring template.
- **Dependencies**: `recurring_template_service`, `request_services`, existing admin auth; relies on `RequestAttribute` tagging.
- **Changes**:
  - Add a helper (e.g., `archive_runs_for_template(session, template_id, acting_user)`) that queries `RequestAttribute` for the template key, filters to published (non-draft/pending) `help_requests`, updates their status to archived/completed, and records an audit entry.
  - Expose a POST route under `/requests/recurring/{template_id}/archive` (admin-only) that invokes the helper, returning totals for UI feedback.
  - Ensure the helper works in batches to avoid timeouts (>200 rows).
- **Verification**: Manual API call via `httpie` or FastAPI test client; confirm response includes count and that linked requests now show archived status.
- **Risks**: Large templates may still take >5s; missing attributes mean some runs remain untouched (documented). Ensure idempotency if endpoint retried.

## Stage 2 – Admin UI affordance + confirmation
- **Goal**: Let admins trigger the archive from `/requests/recurring` with a confirmation modal summarizing the impact.
- **Dependencies**: Stage 1 endpoint; template list component; alert/toast styles.
- **Changes**:
  - Update `templates/requests/recurring.html` and its JS (if any) to render an admin-only “Archive runs” button per card plus a modal (reuse existing modal partial if available) showing run count/date range (fetched via new endpoint or embedded data attribute from server-provided counts).
  - Wire the modal confirm action to POST the Stage 1 route (Fetch API), show loading state, then surface success/error toast and refresh the template card (or entire page).
- **Verification**: Manual browser test as admin: open modal, confirm counts, submit, observe success toast and verify that linked requests disappear from main requests list after refresh.
- **Risks**: Counting runs client-side may require an extra API call; ensure half-auth viewers don’t see the button; handle CSRF tokens on POST.

## Stage 3 – Audit & logging polish
- **Goal**: Ensure the archive action leaves a clear trail in existing admin logs/interfaces.
- **Dependencies**: Stage 1 data (counts, template id), existing audit log mechanism (e.g., `admin_event_service`).
- **Changes**:
  - Log the archive event with acting admin, template id/title, number of requests affected, and timestamp.
  - Surface recent archive events on the recurring templates page or admin log page if feasible (reuse existing component; otherwise extend log serializer).
  - Document the operation in `docs/plans/recurring_request_archiving_step4_implementation_summary.md` scaffolding for later.
- **Verification**: Trigger archive and inspect admin log output/DB rows to confirm entry content; optionally render the entry in UI if exposed there.
- **Risks**: Log spam if action retried; ensure sensitive data isn’t logged; keep log retrieval performant.
