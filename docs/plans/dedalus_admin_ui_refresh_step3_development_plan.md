# Dedalus Admin UI Refresh – Step 3 Development Plan

## Stage 1 – Panel scaffolding & layout grid
- **Goal**: Split `/admin/dedalus` into two bordered panels (status/actions + API key form) that can stack on mobile and sit side-by-side on desktop.
- **Dependencies**: Current template `templates/admin/dedalus_settings.html`; global layout utilities (section, card, stack, grid classes).
- **Changes**: Wrap existing content in two containers, introduce a responsive grid (e.g., utility class or new CSS) with consistent spacing and headings.
- **Verification**: Load page locally, confirm two panels render with equal gutter, no overlapping content on 1280px and 375px widths.
- **Risks**: CSS conflicts with other admin pages; ensure new classes are namespaced (e.g., `.dedalus-admin`).

## Stage 2 – Verification summary badges & alert placement
- **Goal**: Surface key facts (key stored, last verified, latest job) via colored badges and relocate verification alert inside the status panel header.
- **Dependencies**: Stage 1 containers plus `has_key`, `last_verified`, `verification_message`, job context variables.
- **Changes**: Create summary row with badges (success/warning/error), add small descriptions, move alert markup near summary with contextual icon classes.
- **Verification**: Toggle template context (e.g., fabricate data in dev server) to see success + error states; confirm badges respect dark/light themes.
- **Risks**: Overly verbose badges; keep copy short and fallback text for missing timestamps.

## Stage 3 – Controls + timeline styling
- **Goal**: Keep the `realtime_status` include but make it resemble a timeline and keep Verify / Log controls visually tied to the status panel.
- **Dependencies**: Stage 1 grid, Stage 2 summary.
- **Changes**: Wrap `realtime_status` include in a styled container with timeline classes, add captions, move Verify button + log link into a flex row with spacing; ensure job data attributes unchanged.
- **Verification**: Trigger a verify job locally, watch button state + timeline updates; confirm buttons align and shrink gracefully on mobile.
- **Risks**: Interfering with HTMX/job controls; avoid removing required `data-job-*` attributes.

## Stage 4 – API key management refinements
- **Goal**: Lighten the API key card, add a short summary (key stored? remove behavior), and space inputs consistently.
- **Dependencies**: Stage 1 panel wrappers.
- **Changes**: Add summary text block, clarify checkbox label/help copy, adjust spacing via utility classes, ensure password field + checkbox remain accessible.
- **Verification**: Render both “key stored” and “no key” states; submit form to ensure backend still receives `dedalus_api_key` and `clear_key` values.
- **Risks**: Accidentally altering form name/ids; double-check attributes are unchanged.

## Stage 5 – Responsive polish & accessibility sweep
- **Goal**: Ensure new layout works across breakpoints and passes basic a11y review.
- **Dependencies**: All prior stages.
- **Changes**: Add CSS media queries if needed for grid collapse, verify headings/focus order/aria labels, ensure contrast tokens applied to badges and alerts.
- **Verification**: Manual browser resize tests, keyboard navigation through the page, light/dark theme check.
- **Risks**: Forgetting smaller breakpoints; add TODO for future if more than CSS tweak is needed.
