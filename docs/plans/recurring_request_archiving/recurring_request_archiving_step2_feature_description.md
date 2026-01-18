# Recurring Request Archiving — Step 2 Feature Description

## Problem
Admins must currently archive recurring runs one-by-one, so closing out long-running chores or monthly requests is tedious and error-prone.

## User stories
- As an admin, I want to open a recurring template and archive every published run it produced, so I can clear the board after a cycle completes.
- As an admin, I want to review how many requests will be affected before I confirm the bulk archive, so I feel confident about the action.
- As an admin, I want the template to stay visible with updated metadata (last run, next run, paused state) after archiving its runs, so I can decide whether to resume it later.

## Core requirements
- Surface a template-level action (e.g., “Archive published runs”) on the recurring templates UI for admins only.
- Show a confirmation dialog summarizing the number of published requests that will be archived and the date range covered.
- When confirmed, archive every `help_requests` row tagged with the template’s `recurring_template_id`, skipping drafts/pending runs.
- Update the onscreen template list to reflect the action (success toast or refreshed state) without requiring a manual reload.
- Log the archive event for auditing (existing admin log or template activity feed).

## Shared component inventory
- **Recurring templates list (`templates/requests/recurring.html`)**: reuse the existing card layout and template metadata slots; extend with an admin-only action button and modal.
- **Admin toast/alert component**: reuse the global alert/toast styles already triggered by other actions on the page for confirmation feedback.
- **Request serialization**: rely on `RequestAttribute` metadata (already loaded in `_render_requests_page`) instead of introducing new payloads.

## User flow
1. Admin opens `/requests/recurring` and sees the template list with an extra action on each card.
2. Admin clicks “Archive runs” on a template.
3. A dialog appears summarizing how many published requests are linked and the date span; admin confirms.
4. Server runs the bulk archive, returns success/failure.
5. UI shows confirmation and refreshes the template row (and optionally the requests list if already on screen).

## Success criteria
- Admin can archive 100% of published runs for a template in ≤2 clicks without visiting individual request pages.
- Bulk archive skips drafts/pending runs while leaving the template intact and ready for future schedules.
- Action completes within 5 seconds for up to ~200 linked requests in manual testing (document any longer paths).
- Audit log includes an entry identifying the admin, template, and number of archived requests.
