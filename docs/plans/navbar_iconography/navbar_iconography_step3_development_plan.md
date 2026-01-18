# Navbar Iconography · Step 3 Development Plan

## Stage 1 – Icon set & placement audit
- **Goal**: Identify the exact links/cards needing icons and confirm sizing/spacing constraints.
- **Changes**: Inventory `account_nav.html` primary links, mobile panel links, and `menu/index.html` cards. Decide on final icon list (Requests, Comments, Browse, Menu). Sketch desired placement (left of text) and note existing CSS hooks to reuse.
- **Verification**: Annotated checklist showing each surface + icon slot.

## Stage 2 – Create/reuse inline SVG components
- **Goal**: Produce the four SVG icons with consistent stroke weight and theme-aware fills.
- **Changes**: Add SVG partials (e.g., `templates/partials/icons/icon_requests.svg`) or inline macros that output minified SVG with `currentColor`. Ensure `aria-hidden="true"` and optional `<title>` for clarity.
- **Verification**: Render each icon standalone in a simple template to confirm sizing (16–18px) and color inheritance.

## Stage 3 – Update navbar + mobile markup
- **Goal**: Insert icons before link labels in `account_nav.html` and the mobile nav panel.
- **Changes**: Wrap link text in `<span>` and include the SVG partial ahead of it. Add a wrapper class (`account-nav__link-icon`) for spacing.
- **Verification**: Manual UI check on desktop + mobile to ensure icons align, link hitboxes stay intact, and screen readers still read only the text label.

## Stage 4 – Update Menu page cards
- **Goal**: Add the matching icons to key cards on `menu/index.html` (Requests workspace, Comments, Browse, etc.).
- **Changes**: Include the relevant SVG before each card title. Adjust card CSS if needed for alignment.
- **Verification**: Load `/menu` and confirm icons render consistently with the navbar style.

## Stage 5 – Styling + QA
- **Goal**: Add any necessary CSS tweaks and verify accessibility.
- **Changes**: Update `static/skins/base/10-navigation.css` and menu styles with icon spacing, ensure `display: inline-flex` for link wrappers, and test theme toggles. Run through keyboard navigation and mobile view.
- **Verification**: Manual QA checklist + screenshots; ensure final Step 4 summary documents icon reuse across nav and Menu.
