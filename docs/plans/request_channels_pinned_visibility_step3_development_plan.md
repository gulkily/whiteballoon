# Request Channels Pinned Visibility — Step 3 Development Plan

1) Stage 1: Add priority area to the sidebar layout
- Goal: Create a dedicated UI region above the filters for pinned/active channels and remove the hidden-active warning.
- Dependencies: `templates/requests/channels.html`; existing request-channel card markup.
- Expected changes: Introduce a priority container and list hook in the sidebar; remove the filter notice block; ensure the priority area uses the same request-channel card structure; no database changes.
- Verification approach: Load `/requests/channels` and confirm the warning text is gone and the new priority container renders.
- Risks or open questions: Decide whether to extract the channel card markup into a shared partial for reuse or clone via JS.
- Canonical components/APIs touched: request channel card markup, sidebar layout, filter toolbar, result count label.

2) Stage 2: Update client-side channel list logic for priority entries
- Goal: Keep pinned and (if filtered out) active conversations visible in the priority area while maintaining clean filter behavior in the main list.
- Dependencies: `static/js/request-channels.js`; existing request metadata in `state.requests` and `channelMeta`.
- Expected changes: Add priority list references; build/refresh priority entries on filter/search and on channel selection; ensure priority entries are not duplicated when visible in the filtered list; remove `updateFilterNotice` usage; extend event binding and presence updates to include priority entries as needed; no database changes.
- Verification approach: Toggle filters/search, confirm pinned always appears in priority; confirm active appears only when missing from filtered list; ensure result count reflects filtered list only; verify clicking priority entries loads the channel.
- Risks or open questions: Remote search results might omit pinned/active metadata—confirm cached source of truth; decide whether priority entries should participate in keyboard navigation.
- Canonical components/APIs touched: request channel card behavior, filter/search logic, presence indicators, result count.

3) Stage 3: Style the priority area to match the list
- Goal: Make the priority block feel like a deliberate, aligned extension of the sidebar.
- Dependencies: `static/skins/base/30-requests.css`.
- Expected changes: Add spacing, layout, and optional divider styles for the priority area; ensure request-channel cards render consistently; no database changes.
- Verification approach: Visual check on desktop and mobile to confirm the priority area sits above filters and remains readable.
- Risks or open questions: Added vertical space could push the list down too far on smaller screens.
- Canonical components/APIs touched: sidebar layout styles, request channel card styles.
