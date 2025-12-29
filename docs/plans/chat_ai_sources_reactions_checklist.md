# Ask AI Sources – Reaction Formatting Checklist

- [x] Extend `app/services/chat_ai_service.py` so request/comment citations include a `reaction_summary` payload (list of `{emoji, count}`) derived from the strip helper.
- [x] Update `/api/chat/ai` (`app/routes/chat_ai_api.py`) to expose the new field via `ChatAICitation`, ensuring backward compatibility for existing consumers.
- [x] Adjust `static/js/chat-ai-panel.js` (and any required CSS) to render the summary beneath each snippet using the same `meta-chip` badges as other reaction displays.
- [ ] Manually verify the Ask AI panel (channels page + AI search results) shows the cleaned reactions without double escaping or layout regressions.
