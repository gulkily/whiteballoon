# Navbar Enhancements · Step 3 Development Plan

## Stage 1 – Audit data/context needs
- **Goal**: Confirm which session/menu details are required after the layout change.
- **Dependencies**: None.
- **Changes**: Review `templates/partials/account_nav.html`, `app/routes/ui/__init__.py`, and menu context helpers to map which variables drive nav links, admin badge, avatar, etc. Document any gaps (e.g., missing link slugs) to feed into Stage 2.
- **Verification**: Annotated checklist noting existing context fields and confirming Menu page already has Sign Out.
- **Risks**: Overlooking a template include that also renders the nav; mitigate by grepping for `account_nav` usage.

## Stage 2 – Restructure navbar markup
- **Goal**: Split the navbar into primary links (left) and utility rail (right) with a single admin badge.
- **Dependencies**: Stage 1 audit complete.
- **Changes**: Rewrite `account_nav.html` to introduce two flex containers: primary nav (Requests, Comments, Browse/People, Menu) and utility section (avatar, username, single Admin chip, notifications if applicable). Remove redundant admin label near username.
- **Verification**: Run server locally and inspect desktop layout; confirm only one Admin chip is visible.
- **Risks**: Breaking existing include blocks (e.g., login state). Keep anonymous state unchanged.

## Stage 3 – Update navigation styles
- **Goal**: Ensure the new layout looks consistent and responsive.
- **Dependencies**: Stage 2 markup landed.
- **Changes**: Adjust `static/skins/base/10-navigation.css` (and theme overrides) to style the split sections, align link buttons, and define responsive behavior (wrap/stack on narrow widths). Add consistent spacing/typography per Step 2 requirements.
- **Verification**: Manual browser testing at desktop + mobile widths; confirm the utility rail reflows without overlap.
- **Risks**: Global nav CSS regressions; scope selectors to the nav wrapper to avoid affecting other components.

## Stage 4 – Move Sign Out to Menu page
- **Goal**: Remove Sign Out from the nav and surface it inside the Menu page (and optional avatar dropdown if desired).
- **Dependencies**: Stage 2 ensures nav no longer needs the button.
- **Changes**: Delete the Sign Out link/button from `account_nav.html`; add a clearly styled Sign Out entry to `templates/menu/index.html` (reuse existing button styles). Ensure CSRF token/form still works.
- **Verification**: Click Sign Out from Menu page to confirm logout flow works; verify no Sign Out control remains in navbar.
- **Risks**: Users might miss the new location if Menu lacks prominence; consider highlighting the Menu link text/icon.

## Stage 5 – Polish + responsive QA
- **Goal**: Validate consistency and capture documentation.
- **Dependencies**: Prior stages done.
- **Changes**: Manual QA checklist covering admin vs non-admin views, mobile nav behavior, Menu page content. Update any relevant docs (e.g., README snippet if it references navbar). Draft Step 4 implementation summary with verification notes.
- **Verification**: Screenshots or notes from desktop/mobile runs, plus updated Step 4 doc.
- **Risks**: Missing an edge role (half-auth, logged-out). Ensure QA includes those states.
