# Members Directory Display Names

## Goal
Render the same friendly display names on `/members` that already appear in the chat log at `/requests/channels`, so members see “Chengyi” instead of `signal-harvard-st-commons-chengyi`.

## Reference implementation
- `templates/requests/partials/channel_message.html` sets `display_name = comment.display_name or chat.comment_display_names.get(comment.user_id) or '@' ~ comment.username` before rendering each message author.
- `_load_signal_display_names_for_user_ids` (inside `app/routes/ui/__init__.py`) pulls the `signal_display_name:<slug>` attributes so the `chat.comment_display_names` map is available to the template.

## Members directory approach
1. Added `user_attribute_service.load_display_names(session, user_ids)` which mirrors the chat lookup by reading the latest `signal_display_name:*` attribute for each user that appears on the current page.
2. `app/routes/ui/members.py` now gathers the visible profile IDs, loads their display names via the helper, and passes the `member_display_names` map to the template (next to the existing avatar map).
3. `templates/members/index.html` mirrors the comment template by computing `profile_display_name = member_display_names.get(profile.id) or profile.display_name` before invoking `partials/display_name.html`, ensuring the reusable component receives the resolved value.

This keeps `/members` in lockstep with the comments UI: if a user has a Signal-derived display name, we render it; otherwise the component falls back to `@username`, exactly like chat messages do.
