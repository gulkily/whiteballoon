# Request/Comment Action Menu — Step 2 Feature Description

## Problem
Request and comment cards currently surface actions (mark completed, promote, copy link, upcoming pin/unpin, etc.) as independent buttons or chips. This clutters the layout, competes with member-visible metadata, and makes it difficult to add future controls—whether for admins or regular members—without degrading consistency.

## User Stories
- As an admin, I can open a compact actions menu on any request card to access contextual controls (e.g., pin, complete) without new buttons appearing inline.
- As an admin, I can access the same pattern on comment cards when moderation or promotion actions are available.
- As a community member, I can still open the menu (even if only member-level actions exist) so the trigger feels consistent for everyone.
- As a keyboard user, I can tab to the actions trigger, open the menu, move between items, and close it with Escape or by leaving focus.

## Core Requirements
- Provide a reusable template partial that renders a standardized trigger button (likely icon-only) plus a menu list; both request and comment cards should include it.
- Use a lightweight JavaScript helper to manage open/close state, focus trapping, outside click handling, and ARIA attributes so menus meet accessibility expectations.
- Ensure only one menu is open at a time; opening another should close the previous one automatically.
- Menu items are declarative (callable from the parent template) so features like “Pin request” or “Promote comment” can register entries without duplicating markup.
- Respect permissions on a per-action basis; hide the trigger only when *no* actions (member or admin) are available.
- Style the trigger/menu so it blends with existing `meta-chip` aesthetics while remaining clearly interactive and discoverable.

## Shared Component Inventory
- `templates/requests/partials/item.html`: request card markup will include the action-menu partial instead of ad-hoc buttons in its footer/header.
- `templates/partials/comment_card.html`: comment cards already accept an `actions` slot; this will switch to the shared menu component for moderation controls.
- `static/js/request_form.js` (or new module under `static/js/`): host the action-menu JS controller; ensure it initializes on both request and comment contexts.
- `static/skins/base/*.css`: house menu styling (trigger icon, dropdown panel) alongside existing request/comment styles to keep skins consistent.

## User Flow
1. Admin hovers or focuses on a request/comment card and sees the standard actions trigger (e.g., “⋯” button) in the header/footer.
2. Clicking or pressing Enter/Space on the trigger opens the menu aligned to the card; focus moves into the first actionable item.
3. Admin selects an action (click/Enter) or presses Escape to close; the menu dispatches the existing action handler (form submit, modal, fetch, etc.).
4. Clicking elsewhere or opening another menu automatically closes the current one to avoid overlapping panes.
5. If a user has at least one action (member or admin), the trigger is visible and behaves the same; when no actions are available the trigger is omitted entirely.

## Success Criteria
- Both request and comment cards render a uniform action trigger only when actions exist; otherwise, there’s no visual change for regular users.
- Menu supports keyboard navigation (Tab/Shift+Tab stay within the menu, Escape closes, Enter activates items).
- Only one menu stays open at a time, and clicking outside closes it within ~100ms.
- Documentation (e.g., dev cheatsheet or component notes) explains how to register menu items from future features.
- Manual verification confirms the menu works in Chrome/Firefox (desktop) and is discoverable/tappable on mobile.
