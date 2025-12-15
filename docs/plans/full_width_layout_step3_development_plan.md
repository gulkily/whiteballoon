# Full-width Layout · Step 3 Development Plan

## Stage 1 – Container audit
- **Goal**: Map where `.container` and related wrappers appear (base template, sections, nested cards) and flag any pages needing special treatment.
- **Changes**: Grep through `templates/` for `.container`, catalog pages with nested containers (menu, admin dashboards, request feed). Note any components that should stay narrow.
- **Verification**: Checklist capturing pages + decisions (full-width vs. narrow utility).

## Stage 2 – Update global container styles
- **Goal**: Make the base `.container` span the viewport width with responsive padding.
- **Changes**: Adjust `static/skins/base/00-foundations.css` (or the relevant CSS file) to set `max-width: 100%`, use `padding-inline` clamps (e.g., `max(1rem, 5vw)`), and update the nav container to match.
- **Verification**: Manual inspection on desktop/mobile to confirm the main layout stretches without breaking.

## Stage 3 – Introduce `.container--narrow` utility
- **Goal**: Provide an opt-in class for sections/forms that need a constrained width.
- **Changes**: Add CSS for `.container--narrow` (e.g., max-width 800px centered). Update templates that need it (settings forms, auth pages) to apply the class.
- **Verification**: Ensure narrow sections retain previous appearance while the rest of the layout stays full-width.

## Stage 4 – Clean up nested containers
- **Goal**: Remove redundant inner `.container` wrappers on pages like Menu, admin dashboards, etc., to avoid double padding.
- **Changes**: Update affected templates to rely on the new global container instead of rolling their own; adjust spacing using utility classes where needed.
- **Verification**: Load each modified page, check for consistent gutters and no horizontal scroll.

## Stage 5 – QA + documentation
- **Goal**: Validate across breakpoints and record the change.
- **Changes**: Manual QA on desktop ultrawide, laptop, and mobile. Verify sticky nav alignment, modals, and forms. Document findings in Step 4 summary and note any follow-up needs.
- **Verification**: Screenshots or notes from the QA run.
