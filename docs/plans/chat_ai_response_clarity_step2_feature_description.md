# Chat AI Response Clarity - Step 2 Feature Description

Problem: The AI response intro paragraph currently repeats the full list of source titles, even though the Sources list already shows them, which makes the answer hard to scan.

User stories:
- As a member, I want a concise summary response so I can understand the answer quickly before reviewing sources.
- As a member, I want the Sources list to remain intact so I can verify the supporting requests and chats.
- As an operator, I want the AI response format to stay consistent across questions so the panel feels predictable.

Core requirements:
- The intro response should not enumerate the full list of titles already present in Sources.
- The Sources list remains the canonical, unchanged list of linked items.
- The response includes a short narrative summary of what matched (or a clear no-match/guardrail message).
- Behavior is consistent regardless of request/chat scope selection.

Shared component inventory:
- Web AI panel response transcript (Request Channels page): reuse the existing transcript UI; change only the assistant message content.
- Web AI panel Sources list: reuse as-is; no new list or duplication in the response body.
- `/api/chat/ai` response payload: reuse existing schema; adjust only the response text content.

Simple user flow:
1. Member opens Request Channels and asks a question in the AI panel.
2. Assistant replies with a brief summary (no full title list).
3. Sources list shows the full set of linked requests/chats for inspection.
4. Member opens any source link as needed.

Success criteria:
- The assistant response no longer includes the full list of source titles.
- The Sources list appears unchanged and still contains all matched items.
- Users can scan the answer faster without losing access to evidence.
