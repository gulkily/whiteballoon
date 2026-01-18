# Draft Requests · Step 3 Development Plan

**Step 3 reminder**: Break work into atomic stages (~≤1 hr / ≤50 LoC) with goal, dependencies, changes, verification, risks, and call out canonical components (schema, templates, APIs) so nothing forks silently. Capture verification approach (manual OK) and flag any stage still too large.

## Stage 1 – Add `draft` status + filtering guardrails
- **Goal**: Extend `HelpRequest` to support a `draft` state and ensure all existing list/detail queries automatically exclude drafts unless explicitly asked for the author.
- **Dependencies**: None.
- **Changes**: Update `app/models.py` to document the allowed statuses (`draft`, `open`, `completed`, etc.). Adjust shared query builders or SQLModel statements in `app/routes/ui/__init__.py`, `requests` data helpers, and any exports (search for `help_requests` queries) to add `status != 'draft'` filters by default. Confirm templates like `templates/requests/partials/item.html` and API serializers keep `status` available for later UI logic but only surface non-drafts to other users.
- **Verification**: Run existing request feed (UI + `/api/requests`) and confirm the payload omits draft rows while published requests still render. Unit smoke: create a draft entry manually in DB and ensure it doesn’t appear in admin/export queries.
- **Risks**: Missing a query (e.g., admin dashboards) could leak drafts; mitigate by grepping for `HelpRequest` select statements and adding centralized helpers.

## Stage 2 – Draft CRUD endpoints (author-scoped)
- **Goal**: Provide API + server handlers so authenticated users can create, update, list, publish, and delete their drafts using the existing `HelpRequest` row.
- **Dependencies**: Stage 1 status support.
- **Changes**: In `app/routes/ui/requests.py` (and any `app/routes/*` API modules), implement endpoints such as `POST /api/requests/drafts` (create/update), `GET /api/requests/drafts` (list current user’s drafts ordered by `updated_at`), `POST /api/requests/{id}/publish` (status flip to `open`), and `DELETE /api/requests/{id}` for drafts only. Reuse existing validation helpers, ensure ownership checks, and return the same schema used by request-feed so the UI can reuse serialization. Wire routes into FastAPI app via `app/routes/ui/__init__.py`.
- **Verification**: Manual curl/HTTPie tests creating a draft, listing, publishing, and deleting, ensuring non-authors receive 404/403 for others’ drafts. Ensure successful publish triggers `updated_at` and `created_at` semantics expected by feed.
- **Risks**: Accidentally allowing publishes without required fields or letting non-authors operate on drafts; mitigate with explicit ownership filters and `status == 'draft'` assertions per action.

## Stage 3 – Requests page template + drafts list
- **Goal**: Surface draft controls within the canonical Requests page without duplicating markup.
- **Dependencies**: Stages 1–2.
- **Changes**: Update `templates/requests/index.html` to add Save draft / Publish buttons on the hero form, plus a new drafts section (card stack) rendered only when the current user has drafts. Reuse `templates/requests/partials/item.html` styles for description snippets but wrap in a draft-specific list to avoid mixing with live feed. Add edit links that populate the form via data attributes (no new template). Ensure the new section references canonical components (e.g., action menu partial) when offering Delete/Publish buttons.
- **Verification**: Load the page with mocked drafts (via template context) and confirm list renders only for the author; inspect markup to ensure accessibility (aria labels, button semantics) match existing components.
- **Risks**: Template conditional errors causing drafts section to flash to other users; mitigate by scoping context variable to the authenticated user in the route.

## Stage 4 – `request-feed.js` enhancements for drafts
- **Goal**: Extend the existing JS controller to drive Save draft, edit draft, publish, and delete flows while keeping published request behavior intact.
- **Dependencies**: Stage 3 template markup + Stage 2 endpoints.
- **Changes**: Update `static/js/request-feed.js` to: (1) add listeners for new Save draft button (POST to `/api/requests/drafts`), (2) support populating the form when an Edit draft action is clicked (store `data-draft-id`), (3) handle Publish (POST to `/api/requests/{id}/publish`) and Delete (DELETE) actions from the drafts list, and (4) refresh the drafts + main request lists without full reload when actions complete. Keep API base constant centralized and reuse `refreshVisibleLists()` by adding a companion `refreshDrafts()` helper for the new section. Ensure status messaging uses the existing `data-request-status` node.
- **Verification**: Browser manual test: create draft, edit, publish, delete, ensuring toasts/status text update and that the published request appears without duplicates. Confirm `request-feed` behavior for pinned/public requests is unchanged by running through main share form.
- **Risks**: Race conditions causing state loss if Save + Publish happen quickly; mitigate by disabling buttons during async ops and clearing local `draftId` state after publish.

## Stage 5 – Privacy + regression QA / documentation
- **Goal**: Validate end-to-end behavior and capture implementation notes per Step 4 requirements.
- **Dependencies**: Stages 1–4 complete.
- **Changes**: Perform manual QA with two user accounts (author vs other member) to confirm drafts stay private, publishes show up in all feeds, and exports/admin screens remain unaffected. Update any relevant docs (e.g., `FEATURE_DEVELOPMENT_PROCESS` Step 4 summary prep or `docs/plans/README.md` if a new folder is created). Begin drafting Step 4 implementation summary skeleton with verification notes.
- **Verification**: QA checklist results + screen captures if helpful; confirm automated linters/tests still pass.
- **Risks**: Missing a data export or older API path; mitigation is to include admin/export routes in the QA checklist before closing the stage.
