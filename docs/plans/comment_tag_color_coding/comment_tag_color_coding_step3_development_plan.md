# Comment Tag Color Coding · Step 3 Development Plan

## Stage 1 – Compute deterministic hues server-side
- **Goal**: Produce a stable `tag_hue` for every resource/request tag slug.
- **Dependencies**: None.
- **Changes**:
  - Add a small helper (e.g., `app/services/tag_color_service.py`) that takes a slug, hashes it (md5), returns hue `0-359` plus cached CSS-ready `"--tag-hue"` string.
  - Update `comment_llm_insights_service.CommentInsight` → add computed hue list properties (e.g., `resource_tag_colors = [(tag, hue), …]`) when serializing.
- **Verification**: Manual REPL call (`python -m app.tools.tag_color_debug housing`) showing same hue for repeated invocations.
- **Risks**: Forgetting to normalize slugs to lower case would yield inconsistent colors; mitigate by lowercasing in helper.

## Stage 2 – Thread hue metadata through templates and APIs
- **Goal**: Ensure every surface that renders insight tags receives the hue values.
- **Dependencies**: Stage 1 helper available.
- **Changes**:
  - Amend `_build_comment_insights_lookup`, `_build_request_comment_insights_summary`, and promoted-comment context builders to include `tag_hues` (or embed colorized chip context) per tag.
  - Extend admin comment insight API payload to include `color` alongside each tag string so `comment-insight-badges.js` can render colored chips.
  - Update Jinja contexts (`templates/comments/detail.html`, `requests/detail.html`, `partials/comment_card.html`) to consume `(label, hue)` pairs instead of plain strings.
- **Verification**: Load request detail and comment permalink in dev server with dummy data showing JSON includes `tagHue` and Jinja loops render attributes.
- **Risks**: Missing hue in any context causes template errors; add defaults/fallback values when metadata absent.

## Stage 3 – Update shared meta-chip styling with CSS variables
- **Goal**: Color chips via CSS custom properties so skins control saturation/lightness.
- **Dependencies**: Stage 2 adds `data-tag-hue` (or inline style) to DOM.
- **Changes**:
  - Add CSS to base skin (and overrides for alt skins) that reads `data-tag-hue`/`style="--tag-hue"` and sets background/text colors using `hsl(var(--tag-hue), var(--tag-saturation), var(--tag-lightness))`.
  - Define skin-level `--tag-saturation`, `--tag-lightness`, `--tag-text-color` tokens.
  - Ensure fallback styling applies when `data-tag-hue` missing.
- **Verification**: `npm run dev` (or static build) + manual inspection; confirm contrast via browser dev tools.
- **Risks**: Poor contrast on dark skin; mitigate by testing and adjusting skin overrides before shipping.

## Stage 4 – JavaScript badge rendering parity
- **Goal**: Match server-rendered chip colors inside `static/js/comment-insight-badges.js` overlays.
- **Dependencies**: Stage 2 API includes hue/color data; Stage 3 CSS handles styling when attributes present.
- **Changes**:
  - Update render function to output the same `data-tag-hue` (or inline `style="--tag-hue: …"`) for each chip.
  - Ensure escaping remains intact and fall back to neutral chip if payload lacks hue.
- **Verification**: Trigger badge popover in browser and confirm colors align with on-page chips.
- **Risks**: Missing escaping introduces XSS risk; keep using `escapeHtml` for both text and attribute values.

## Stage 5 – Regression sweep and documentation
- **Goal**: Verify all tag surfaces and document the deterministic color behavior.
- **Dependencies**: All prior stages implemented.
- **Changes**:
  - Manually test request detail, comment detail, promoted comment card, admin insights badge, and API JSON (via curl) to confirm hue propagation.
  - Update relevant docs (`docs/plans/README.md` or internal design tokens note) describing the hashing approach and CSS variables for future contributors.
- **Verification**: Checklist in Step 4 summary; capture screenshots or notes confirming each surface.
- **Risks**: Overlooking a surface; mitigate with explicit checklist referencing every template/JS file touched earlier.
