# Caption Personalization · Step 3 Development Plan

**Step 3 reminder**: Keep stages small (~≤1 hr / ≤50 LOC), document goal, dependencies, changes, verification, and risks. Highlight shared components touched to avoid forks.

## Stage 1 – Data layer for caption preferences
- **Goal**: Persist per-user global toggle + per-caption dismissals.
- **Dependencies**: None.
- **Changes**: Extend user settings storage (likely `user_attributes` table) with keys like `ui_hide_captions` and `ui_caption_dismissals` (JSON of caption IDs). Add helper functions in a new `app/services/caption_preference_service.py` to get/set these values.
- **Verification**: REPL test storing/retrieving preferences for a sample user.
- **Risks**: JSON size growth; keep IDs short and add pruning when clearing.

## Stage 2 – Caption rendering helper
- **Goal**: Create a reusable component (Jinja macro + Python helper) that wraps caption text with the thumbs-up button and respects preferences.
- **Dependencies**: Stage 1 service.
- **Changes**: Add `app/ui/captions.py` (or similar) with `render_caption(request, caption_id, text)` that checks global toggle + dismissals and returns markup. Create a Jinja macro file `templates/partials/caption.html` to render the UI, including data attributes for JS.
- **Verification**: Template unit test via `jinja2` render or manual snippet showing caption hidden when service says so.
- **Risks**: Forgetting to include accessibility labels; ensure button has aria-label.

## Stage 3 – Global toggle UI in settings
- **Goal**: Let users enable/disable all helper captions via account settings.
- **Dependencies**: Stage 1 data layer.
- **Changes**: Update `settings/account` route + template to add a checkbox (e.g., “Hide helper captions”), post handler writes `ui_hide_captions`, plus a “Reset caption dismissals” button that clears the JSON map.
- **Verification**: Manual test toggling the checkbox and confirming value persists + captions disappear after page reload.
- **Risks**: Confusing label; include helper copy clarifying what “helper captions” means.

## Stage 4 – Per-caption dismiss endpoint + JS
- **Goal**: Hook up the 👍 “Got it” button to persist dismissals without a full reload.
- **Dependencies**: Stages 1–2.
- **Changes**: Add POST route (e.g., `/api/captions/{caption_id}/dismiss`) that writes to preferences, returning JSON. Create a tiny JS module (`static/js/captions.js`) that attaches click handlers to `[data-caption-dismiss]` buttons, calls fetch POST, and hides the caption on success.
- **Verification**: Manual click test on a caption; ensure subsequent reload keeps it hidden.
- **Risks**: Many captions on a page -> too many fetches; degrade gracefully (buttons still submit form if JS fails).

## Stage 5 – Integrate helper into sample surfaces
- **Goal**: Replace hard-coded helper text blocks with the new caption helper on key pages.
- **Dependencies**: Stages 2–4.
- **Changes**: Identify at least three existing captions (Requests hero blurb, menu quick access text, invite explanation) and wrap them with the macro. Ensure each has a unique caption ID defined centrally.
- **Verification**: Manual UI pass verifying captions render + hide/dismiss as expected in both states.
- **Risks**: Missing caption IDs or collisions; maintain a registry constant for unique names.

## Stage 6 – QA + docs
- **Goal**: Validate end-to-end scenarios and document usage for future captions.
- **Dependencies**: Prior stages.
- **Changes**: QA checklist covering: new user (captions visible), dismiss single caption, toggle world-off, reset dismissals. Update developer docs (e.g., `DEV_CHEATSHEET` or README) with instructions on adding new caption IDs and using the helper. Summarize in Step 4 doc.
- **Verification**: QA notes + Step 4 write-up.
- **Risks**: Cross-browser JS behavior; sanity-check in at least Chrome + one other browser.
