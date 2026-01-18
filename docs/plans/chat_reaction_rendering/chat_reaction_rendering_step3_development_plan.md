# Chat Reaction Rendering – Step 3: Development Plan

1. **Confirm reaction text patterns**  
   - Dependencies: Step 2 user stories; existing Signal-imported messages.  
   - Expected changes: survey a handful of messages to catalog edge cases (multiple emojis per person, different separators, missing closing parenthesis) and note them in the Step 4 summary.  
   - Verification: manual inspection of `/requests/30` history plus at least one search result; no automated tests.  
   - Risks: unexpected formats could break parsing; documenting them upfront minimizes surprises.  
   - Components touched: planning doc only.  

2. **Add reaction parser utility**  
   - Dependencies: Stage 1 findings.  
   - Expected changes: create a helper (e.g., `app/services/chat_reactions.py` or a function inside `request_chat_search_service`) that accepts a message string and returns `(clean_body, [{emoji, count, names?}])`.  
   - Verification: interactive Python shell runs with sample strings; confirm fallback when pattern absent.  
   - Risks: performance impact negligible; main risk is false positives if a real message ends with “(Reactions: …)”.  
   - Components touched: backend helper module.  

3. **Expose parsed reactions to channel templates**  
   - Dependencies: Stage 2 helper.  
   - Expected changes: update the data shape passed to `templates/requests/partials/channel_message.html` (and search API) to include `clean_body` + `reaction_summary`. Could happen either in the backend when building `chat.comments` or in the template via a Jinja filter.  
   - Verification: load `/requests/channels?channel=<id>` and ensure debug output shows the new fields.  
   - Risks: mutating message bodies directly; ensure we only change rendering, not stored text.  
   - Components touched: `app/routes/ui/__init__.py` (chat context builder) or shared filters.  

4. **Render summary in chat/channel templates**  
   - Dependencies: Stage 3 data.  
   - Expected changes: update `templates/requests/partials/channel_message.html` and channel previews/search snippets to display `Reactions: ❤️ ×N` inline (probably beneath message text). Style lightly with existing CSS.  
   - Verification: manual check on `/requests/30`, `/requests/channels`, and search results showing reaction lines stripped from the main body.  
   - Risks: layout crowding in narrow panes; keep summary subtle.  
   - Components touched: templates, maybe CSS.  

5. **Document + regression sweep**  
   - Dependencies: Stage 4 complete.  
   - Expected changes: capture parsing rules/limitations in the Step 4 summary; ensure `rg '(Reactions:'` in rendered HTML no longer finds matches; mention behavior in the dev cheatsheet if needed.  
   - Verification: manual spot checks and search.  
   - Risks: none beyond missing an instance; we can iterate if new formats appear.  
