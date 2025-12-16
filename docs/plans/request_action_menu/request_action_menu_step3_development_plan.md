# Request/Comment Action Menu — Step 3 Development Plan

## Stage 1 – Component scaffolding & CSS tokens
- **Goal**: Define a shared action-menu partial (trigger + menu markup) and baseline styles.
- **Changes**: Create `templates/partials/action_menu.html` (or similar) with slots for trigger label and menu items. Add base styles to `static/skins/base/*.css` for trigger button, dropdown container, and menu items (including focus states and a pinned badge icon placeholder).
- **Verification**: Render the partial in Storybook-like sandbox (temporary template) or add to a dev page and visually confirm layout.
- **Risks**: Styling clashes with existing chips/buttons; ensure CSS variables align with skin tokens.

## Stage 2 – JavaScript controller
- **Goal**: Add a lightweight JS module that handles open/close state, focus management, and outside clicks.
- **Changes**: Create `static/js/action-menu.js` (ES module) that wires to `[data-action-menu]` elements, manages `aria-expanded`, traps focus within the menu, and closes on Escape/outside click. Import/init from existing request/comment JS entry points (or a new `static/js/init-action-menus.js`).
- **Verification**: Manual testing via browser devtools: open menu, tab through items, ensure Escape closes, confirm only one menu stays open when toggling multiple.
- **Risks**: Event listeners leaking (memory) or conflicts with existing JS; mitigate by using delegated listeners and cleaning up on DOMContentLoaded only.

## Stage 3 – Request card integration
- **Goal**: Replace ad-hoc actions on request cards with the shared menu.
- **Changes**: Update `templates/requests/partials/item.html` to include the new partial when `request.actions` (a list of menu entries) is provided. Move "Mark completed" into the menu for authorized admins and add placeholder member actions (e.g., "Copy link"). Adjust server context to supply structured action objects (label, type, href/form) when applicable.
- **Verification**: Load `/requests` as admin and non-admin, confirm the trigger appears only when actions exist, menu items execute the same behaviors as before.
- **Risks**: Regression in existing form submissions; ensure forms inside menu still submit correctly and that progressive enhancement (no JS) falls back to accessible markup (e.g., menu remains visible like a simple list).

## Stage 4 – Comment card integration
- **Goal**: Migrate comment moderation/promotion controls to the same menu component.
- **Changes**: Update `templates/partials/comment_card.html` to use the action-menu partial for comment-specific actions (promotion, insights, future pin). Ensure existing `actions` list is transformed into menu entries and that markup still supports contexts (request view, profile, search variant fallback).
- **Verification**: Visit request detail page with comments; verify menus appear for admins/moderators, hidden for standard users, and actions (e.g., `comment_insight` button) operate as expected.
- **Risks**: Comment contexts differ (variants request/profile/search); guard variants so the menu only appears where actions exist. Ensure the existing "Insights" button remains available if it should stay outside the menu.

## Stage 5 – Documentation & developer guidance
- **Goal**: Document how to register menu actions for future features.
- **Changes**: Update `DEV_CHEATSHEET.md` or a new component note describing the partial, required context data, and JS helper usage. Mention accessibility behaviors and how to add new menu items.
- **Verification**: Markdown review; ensure instructions reference actual filenames and match implementation.
- **Risks**: Docs drifting from code; keep instructions concise and updated when naming changes.
