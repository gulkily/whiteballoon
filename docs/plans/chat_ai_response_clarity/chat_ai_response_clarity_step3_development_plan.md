# Chat AI Response Clarity - Step 3 Development Plan

1. Adjust AI response text composition
   - Goal: Replace the intro paragraph with a concise summary that avoids enumerating every source title.
   - Dependencies: `app/routes/chat_ai_api.py`, `app/services/chat_ai_service.py` (existing context/citation building).
   - Expected changes: Update `_compose_response_text(prompt, context, citations)` to return a short summary message; keep guardrail/no-match messaging intact.
   - Verification: Ask a question in the AI panel and confirm the assistant reply is 1–2 sentences without a numbered list; Sources list still shows all items.
   - Risks/open questions: Ensure the summary remains useful when only comments or only requests match; confirm guardrail text still appears when there are no citations.
   - Canonical components/API: `/api/chat/ai` response format unchanged; AI panel transcript UI reused.

2. Align CLI output with the new response summary
   - Goal: Keep CLI responses consistent with the web panel by avoiding full title lists in the reply text.
   - Dependencies: `app/tools/chat_ai_cli.py`, `app/services/chat_ai_service.py`.
   - Expected changes: Update `_format_response(context)` to mirror the concise summary pattern; keep the CLI "Sources" listing as the canonical list.
   - Verification: Run the CLI prompt and confirm the AI response is a short summary while "Sources" still lists items.
   - Risks/open questions: Confirm CLI users still have enough context without the list inside the response.
   - Canonical components/API: CLI output format only; shared `ChatAIContextResult` stays unchanged.

3. Copy review for AI panel helper text
   - Goal: Ensure the AI panel helper text still sets expectations for short summaries + Sources.
   - Dependencies: `templates/requests/channels.html` (AI panel copy).
   - Expected changes: Optional microcopy tweak to the subtitle or empty state to reinforce that sources list the evidence.
   - Verification: Load the page and confirm copy reads naturally.
   - Risks/open questions: Avoid adding more UI clutter.
   - Canonical components/API: Request Channels page only; no new components.
