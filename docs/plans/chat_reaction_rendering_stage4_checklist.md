# Chat Reaction Rendering – Template Checklist

- [x] `templates/requests/partials/channel_message.html` (chat pane) – render summary row.
- [x] `templates/partials/comment_card.html` (request detail transcript/profile/search) – render summary row.
- [x] `templates/requests/channels.html` sidebar previews – strip suffix via `render_multiline`.
- [x] `templates/requests/partials/channel_chat.html` header/title – normalized multi-line output.
- [x] `templates/requests/detail.html` chat-search template + JS (`static/js/request-chat-search.js`) – render summary line.
- [x] `templates/requests/detail.html` top request card (request description) – still displays raw `(Reactions: …)` text.
- [x] `templates/requests/partials/item.html` (request cards on feed/browse/admin) – still displays raw text.
- [x] `templates/browse/index.html` request cards (if not using `partials/item.html` include) – confirm they inherit cleaned description.
- [x] `templates/requests/channels.html` top request summary card (description) – ensure reaction block removed.
- [ ] `templates/admin/*` and `templates/sync/public.html` surfaces rendering request/comment text – verify they use cleaned fields or add parser.
