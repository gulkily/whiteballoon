## Stage 1 – Backend payload + query parsing
- **Goal**: Provide the necessary data + state for filtering.
- **Dependencies**: `_build_request_detail_context`, `comment_llm_insights_service.list_analyses_for_request`.
- **Changes**:
  - Extend serialized comments with a `insight_metadata` dict containing `resource_tags`, `request_tags`, `urgency`, and `sentiment` (normalized lower-case slugs).
  - Parse new query params (`insight_resource`, `insight_request`, `insight_urgency`, `insight_sentiment`) and pre-filter the `comments` list on the server before rendering.
  - Pass the active filters + available options to the template context for chip state.
- **Verification**: Hit `/requests/{id}?insight_resource=housing` and confirm only matching comments render, no JS required.
- **Risks**: Comment list query already paginates; ensure filtering respects pagination (e.g., apply filters before slicing, or disable pagination when filters are active).

## Stage 2 – Client-side filtering + URL sync
- **Goal**: Provide interactive chip toggles with instant filtering.
- **Dependencies**: Stage 1 data in the DOM.
- **Changes**:
  - Add a small JS module (`comment-insight-filters.js`) that reads chip clicks, toggles active classes, shows/hides comment list items (via data attributes), and updates the query string using `history.replaceState`.
  - When JS loads, it should read any server-supplied filters to initialize chip state without flicker.
  - Include a “Reset filters” button near the insights card.
- **Verification**: Toggle chips, ensure the comment list updates immediately and the URL changes; reloading the page keeps the filters.
- **Risks**: Accessibility—ensure keyboard users can activate chips; avoid layout jumps when many comments hide.

## Stage 3 – Progressive enhancement & multi-select polish
- **Goal**: Handle multi-select chips gracefully and ensure no double-fetches.
- **Dependencies**: Stage 2 JS.
- **Changes**:
  - Support selecting multiple tags/urgencies; JS should combine them (e.g., arrays in query params) and apply conjunction logic on the front end.
  - Optionally add a floating counter “Showing X of Y comments” when filters are active.
  - Debounce `replaceState` updates to avoid spamming history.
- **Verification**: Select multiple chips, confirm counts and hidden comments behave as expected.
- **Risks**: Complexity—limit Stage 3 scope if Stage 2 already meets UX needs.
