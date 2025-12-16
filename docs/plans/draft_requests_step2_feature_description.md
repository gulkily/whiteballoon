# Draft Requests · Step 2 Feature Description

**Problem**: Members have to finish and publish a help request in one sitting; there is no server-side "draft" state, so partially written content can be lost or shared prematurely.

**User stories**
- As a member composing a help request, I want to save it as a draft so I can return later without losing notes.
- As a member reviewing my own work, I want to see a private list of drafts so I can edit or discard them before publishing.
- As a member ready to share, I want to publish a draft in one click so I don't have to retype the same content.
- As an admin/moderator, I want drafts to remain invisible to other users and exports so incomplete or sensitive content never leaks.

**Core requirements**
1. Introduce a `draft` status on `HelpRequest` and ensure the status is only visible/editable by the author until changed to `open` (or other public states).
2. Extend the Requests page form to offer explicit Save draft vs Publish controls, pre-filling the existing fields when editing an in-progress draft.
3. Provide a drafts list (inline on the Requests page) that shows title/description snippets, last-updated time, and quick actions (Edit, Publish, Delete) scoped to the current user.
4. Exclude `draft` requests from all existing public feeds, detail routes, exports, and notifications while still surfacing them through authenticated APIs for the author.
5. Handle optimistic UI feedback (success/error states) for draft saves and publishes so users know whether content was stored.

**Shared component inventory**
- `templates/requests/index.html`: existing request creation card and hero form; will gain Save draft controls, a drafts list section, and edit states instead of duplicating markup elsewhere.
- `static/js/request-feed.js`: powers the form toggles, submission, and list refresh; extend it to support draft save/publish actions and prevent form reset when saving.
- `templates/requests/partials/item.html`: canonical request card used on feeds/detail snippets; keep reusing it when showing published requests and ensure it checks for `draft` status before rendering in shared lists.
- `app/routes/ui/requests.py` + related API handlers: add server endpoints for listing the current user's drafts, saving updates, and toggling status; reuse the existing validation layer instead of new models.
- `app/models.py` (`HelpRequest`): reuse this schema by extending the `status` enum/string to include `draft`; no new table needed per Step 1 recommendation.

**User flow**
1. Authenticated member opens the Requests page and expands the "Share a request" form.
2. They enter an initial description and choose "Save draft"; the UI confirms the draft was stored and collapses into a drafts list showing the new entry.
3. Later, the member selects a draft from the list; the form pre-fills with the draft content for further editing.
4. The member chooses "Publish"; the request status flips from `draft` to `open` and the entry now appears in the main feed for everyone with normal notifications.
5. If the member no longer wants a draft, they can delete it from the drafts list (server removes the `draft` request entirely) without affecting public data.

**Success criteria**
- Members can save at least one draft request, refresh the page, and still see/edit it while signed in as the same user.
- Draft requests never appear in the shared request list, pinned widgets, exports, or comment feeds for other users.
- Publishing a draft immediately makes it visible in the main feed with the same ID and without duplicating content.
- Manual QA confirms saving, editing, publishing, and deleting drafts all display clear status messaging and respect permissions for two distinct user accounts.
