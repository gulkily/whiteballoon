# Request Channels Pinned Visibility — Step 2 Feature Description

Problem: On /requests/channels, filters can hide the pinned or currently viewed conversation, forcing a warning and adding extra steps to reach key threads. The UI should keep priority conversations visible without weakening filter behavior.

User stories:
- As a member, I want the pinned conversation always visible so that I can open it quickly without changing filters.
- As a member, I want the currently viewed conversation visible even if filters exclude it so that I can return to it easily.
- As an admin, I want filters to keep working as expected so that the list stays trustworthy for triage.

Core requirements:
- The pinned conversation is always displayed in a priority area above the filters and list.
- The currently viewed conversation is displayed in the same priority area when it is not present in the filtered list.
- The filtered list continues to show only items that match the active filters, without mixing in priority items.
- The warning message about hidden active requests is removed from the page.
- Priority entries reuse the same metadata and interaction affordances as standard list entries and do not duplicate items already visible in the list.

Shared component inventory:
- Request channels sidebar layout: extend to add a priority area above the filters.
- Channel filter toolbar: reuse as-is; filters still apply to the main list only.
- Request channel card (name, status, time, badges, pinned indicator): reuse; priority entries should use the same component.
- Result count label: reuse; remains tied to the filtered list only.
- Hidden-active warning notice: remove; no replacement needed.

Simple user flow:
1. Member opens /requests/channels and sees the priority area above filters.
2. The pinned conversation appears there; the active conversation appears there if it is filtered out.
3. Member uses filters to narrow the list without affecting the priority area.
4. Member clicks a priority or list entry to open the conversation.

Success criteria:
- Pinned conversation remains visible in the priority area regardless of filters.
- Active conversation appears in the priority area only when it is not in the filtered list.
- No hidden-active warning message appears on /requests/channels.
- Filtered list and result count continue to match the selected filters.
